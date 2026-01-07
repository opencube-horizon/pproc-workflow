import sys
import argparse
import subprocess
import os
import time
import functools
import yaml

from cascade.cascade import Cascade
from cascade.transformers import to_dask_graph
from cascade.graph import pyvis
from ppcascade.parsers import get_parser

import dask
from dask.delayed import Delayed
from dask_kubernetes.classic import KubeCluster, make_pod_spec
from dask.distributed import performance_report


def node_info_ext(sinks, node):
    info = pyvis.node_info(node)
    info["color"] = "#648FFF"
    if not node.inputs:
        info["shape"] = "diamond"
        info["color"] = "#DC267F"
    elif node in sinks:
        info["shape"] = "triangle"
        info["color"] = "#FFB000"
    if node.payload is not None:
        t = []
        if "title" in info:
            t.append(info["title"])
        func, *args = node.payload
        t.append(f"Function: {func}")
        if args:
            t.append("Arguments:")
            t.extend(f"- {arg!r}" for arg in args)
        info["title"] = "\n".join(t)
    return info


def get_kube_logs(namespace, cluster, output_dir):
    env = {
        "HOME": os.environ["HOME"],
        "KUBECONFIG": os.environ["KUBECONFIG"],
        "PATH": os.environ["PATH"],
    }
    subprocess.Popen(
        [
            "kubectl",
            "port-forward",
            f"{cluster.scheduler._pod.metadata.name}",
            "--namespace",
            namespace,
            "8787",
        ],
        env=env,
        stdout=open(f"{output_dir}/scheduler-port-forward.log", "w"),
        stderr=subprocess.STDOUT,
    )
    subprocess.Popen(
        [
            "stern",
            f"{cluster.scheduler._pod.metadata.name}",
            "--namespace",
            namespace,
        ],
        env=env,
        stdout=open(f"{output_dir}/scheduler.log", "w"),
        stderr=subprocess.STDOUT,
    )
    subprocess.Popen(
        [
            "stern",
            "dask-*",
            "--namespace",
            namespace,
            "--exclude-pod",
            f"{cluster.scheduler._pod.metadata.name}",
        ],
        env=env,
        stdout=open(f"{output_dir}/worker.log", "w"),
        stderr=subprocess.STDOUT,
    )


def execute_benchark(config_args, client, cluster, graph):
    from dask.distributed import as_completed

    dask_graph = to_dask_graph(graph)
    outputs = [Delayed(x.name, dask_graph) for x in graph.sinks]

    with performance_report(f"{config_args.output_dir}/performance_report.html"):
        future = client.compute(outputs)

        seq = as_completed(future)
        del future
        # Trigger gargage collection on completed end tasks so scheduler doesn't
        # try to repeat them
        errored_tasks = 0
        for fut in seq:
            if fut.status != "finished":
                print(f"Task failed with exception: {fut.exception()}")
                errored_tasks += 1
            pass

    # Save logs
    if config_args.local:
        logs = client.get_worker_logs()
        for index, (pod, pod_log) in enumerate(logs.items()):
            with open(f"{config_args.output_dir}/worker-{index}.log", "w") as logfile:
                for log_line in pod_log:
                    logfile.write(f"{log_line}\n")
        scheduler_log = client.get_scheduler_logs()
        with open(f"{config_args.output_dir}/scheduler.log", "w") as scheduler_logfile:
            for log_line in scheduler_log:
                scheduler_logfile.write(f"{scheduler_log}\n")

    if errored_tasks != 0:
        raise Exception(f"Completed with {errored_tasks} failed tasks")


def main(args):
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, help="Image for dask workers")
    parser.add_argument(
        "--image_secret",
        type=str,
        help="Kubernetes secret name for pulling image",
        default="",
    )
    parser.add_argument(
        "--kube-namespace", type=str, help="Kubernetes namespace", default="dask"
    )
    parser.add_argument("--node-list", action="extend", nargs="+", type=str)
    parser.add_argument("--output_dir", type=str, help="Directory to write outputs to")
    parser.add_argument("--local", action="store_true", default=False)
    parser.add_argument("--fdb-options", type=str, help="Path to fdb options yaml file")
    config_args, unparsed_args = parser.parse_known_args(args)
    graph_args = get_parser("extreme").parse_args(unparsed_args)

    # FDB options
    with open(config_args.fdb_options, "r") as fdb_options_file:
        fdb_options = yaml.safe_load(fdb_options_file)

    # Create graph
    graph = Cascade.graph("extreme", graph_args)

    # Plot graph
    pyvis_graph = pyvis.to_pyvis(
        graph,
        notebook=True,
        cdn_resources="remote",
        height="1500px",
        node_attrs=functools.partial(node_info_ext, graph.sinks),
        hierarchical_layout=False,
    )
    pyvis_graph.show(f"{config_args.output_dir}/plot.html")

    # Set up distributed client
    dask.config.set(
        {"distributed.scheduler.worker-saturation": 1.0}
    )  # Important to prevent root task overloading
    from dask.distributed import Client

    if config_args.local:
        with Client(
            memory_limit="15G",
            processes=True,
            n_workers=2,
            threads_per_worker=1,
        ) as client:
            execute_benchark(config_args, client, None, graph)
    else:
        # Generate the spec
        extra_pod_config = {
            "volumes": [
                {"name": "cache-volume", "emptyDir": {"sizeLimit": "20G"}},
                {
                    "name": "libcxi",
                    "hostPath": {
                        "path": "/usr/lib64/libcxi.so.1.5.0",
                        "type": "File",
                    },
                },
            ],
            "hostAliases": [
                {
                    "ip": "10.97.3.1",
                    "hostnames": ["infra1", "infra1.can.pt.horizon-opencube.eu"],
                }
            ],
            "securityContext": {"runAsUser": 10012, "runAsGroup": 20013},
            "affinity": {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [
                            {
                                "matchExpressions": [
                                    {
                                        "key": "kubernetes.io/hostname",
                                        "operator": "In",
                                        "values": config_args.node_list,
                                    }
                                ]
                            }
                        ]
                    }
                }
            },
        }
        if config_args.image_secret != "":
            extra_pod_config["imagePullSecrets"] = [{"name": config_args.image_secret}]
        extra_container_config = {
            "volumeMounts": [
                {
                    "mountPath": "/tmp",
                    "name": "cache-volume",
                },
                {
                    "name": "libcxi",
                    "readOnly": True,
                    "mountPath": "/usr/lib64/libcxi.so.1",
                },
            ],
            "env": [
                {"name": var, "value": str(val)} for var, val in fdb_options.items()
            ],
        }

        if fdb_options["FDB_TYPE"] == "local":
            extra_pod_config["volumes"].extend(
                [
                    {
                        "name": "fdb-index",
                        "hostPath": {
                            "path": fdb_options["FDB_HOST_INDEX"],
                            "type": "Directory",
                        },
                    },
                ]
            )
            extra_container_config["env"].extend(
                [
                    {"name": "FI_PROVIDER", "value": "cxi"},
                    {"name": "CXIP_SKIP_AMA_CHECK", "value": "true"},
                    {"name": "FI_CXI_LLRING_MODE", "value": "never"},
                ]
            )
            extra_container_config["resources"] = {
                "requests": {
                    "memory": "15G",
                    "smarter-devices/cxi0": "1",
                },
                "limits": {
                    "smarter-devices/cxi0": "1",
                },
            }
            extra_container_config["volumeMounts"].extend(
                [
                    {
                        "mountPath": fdb_options["FDB_INDEX"],
                        "name": "fdb-index",
                        "mountPropagation": None,
                    },
                ]
            )
        pod_spec = make_pod_spec(
            image=config_args.image,
            memory_limit="15G",
            memory_request="15G",
            cpu_limit=1,
            cpu_request=1,
            extra_pod_config=extra_pod_config,
            extra_container_config=extra_container_config,
        )

        # Create the cluster, allowing it to scale
        cluster = KubeCluster(
            pod_spec,
            namespace=config_args.kube_namespace,
            env={"DASK_LOGGING__DISTRIBUTED": "debug", "PYTHONUNBUFFERED": "1"},
            apply_default_affinity="none",
        )
        cluster.adapt(minimum=1, maximum=5)
        client = Client(cluster)
        get_kube_logs(config_args.kube_namespace, cluster, config_args.output_dir)
        time.sleep(1)
        execute_benchark(config_args, client, cluster, graph)
        client.shutdown()


if __name__ == "__main__":
    main(sys.argv[1:])
