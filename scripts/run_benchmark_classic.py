import sys
import argparse

from cascade.cascade import Cascade
from cascade.transformers import to_dask_graph
from cascade.parsers import get_parser

import dask
from dask.delayed import Delayed
from dask_kubernetes.classic import KubeCluster, make_pod_spec
from dask.distributed import performance_report, LocalCluster


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
    parser.add_argument("--output_dir", type=str, help="Directory to write outputs to")
    parser.add_argument("--local", action="store_true", default=False)
    config_args, unparsed_args = parser.parse_known_args(args)
    graph_args = get_parser("extreme").parse_args(unparsed_args)

    # Create graph
    graph = Cascade.graph("extreme", graph_args)
    dask_graph = to_dask_graph(graph)

    # Generate the spec
    extra_pod_config = {
        "volumes": [{"name": "cache-volume", "emptyDir": {"sizeLimit": "20G"}}]
    }
    if config_args.image_secret != "":
        extra_pod_config["imagePullSecrets"] = [{"name": config_args.image_secret}]
    extra_container_config = {
        "imagePullPolicy": "Always",
        "volumeMounts": [{"mountPath": "/tmp", "name": "cache-volume"}],
    }
    pod_spec = make_pod_spec(
        image=config_args.image,
        memory_limit="30G",
        memory_request="30G",
        cpu_limit=2,
        cpu_request=2,
        extra_pod_config=extra_pod_config,
        extra_container_config=extra_container_config,
    )
    # Create the cluster, allowing it to scale
    if config_args.local:
        cluster = LocalCluster(
            n_workers=2, threads_per_worker=1, processes=True, memory_limit="15G"
        )
    else:
        cluster = KubeCluster(pod_spec)
        cluster.adapt(minimum=1, maximum=2)

    # Set up distributed client
    dask.config.set(
        {"distributed.scheduler.worker-saturation": 1.0}
    )  # Important to prevent root task overloading
    from dask.distributed import Client, as_completed

    client = Client(cluster)
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
    logs = client.get_worker_logs()
    for index, (pod, pod_log) in enumerate(logs.items()):
        with open(f"{config_args.output_dir}/worker-{index}.log", "w") as logfile:
            for log_line in pod_log:
                logfile.write(f"{log_line}\n")
    scheduler_log = client.get_scheduler_logs()
    with open(f"{config_args.output_dir}/scheduler.log", "w") as scheduler_logfile:
        for log_line in scheduler_log:
            scheduler_logfile.write(f"{scheduler_log}\n")

    client.close()
    cluster.close()


if __name__ == "__main__":
    main(sys.argv[1:])
