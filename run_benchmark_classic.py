import os
import subprocess
import socket
import yaml
import sys
import argparse

from cascade.cascade import Cascade
from cascade.graphs import ContextGraph
from cascade.graph_config import Config
from cascade.executor import DaskExecutor
from cascade.transformers import to_dask_graph

import dask
from dask.delayed import Delayed
from dask_kubernetes.classic import KubeCluster, make_pod_spec
from dask.distributed import performance_report


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, help="Image for dask workers")
    parser.add_argument(
        "--image_secret",
        type=str,
        help="Kubernetes secret name for pulling image",
        default="",
    )
    parser.add_argument("--output_dir", type=str, help="Directory to write outputs to")
    image_args = parser.parse_args(args)

    # Create graph
    graph = Cascade.graph(Config("extreme", "configs/extreme.yaml"))
    dask_graph = to_dask_graph(graph)

    # Generate the spec
    extra_pod_config = {}
    if image_args.image_secret != "":
        extra_pod_conifg["imagePullSecrets"] = [{"name": image_args.image_secret}]
    pod_spec = make_pod_spec(
        image=image_args.image,
        memory_limit="16G",
        memory_request="16G",
        cpu_limit=2,
        cpu_request=2,
        extra_pod_config=extra_pod_config,
    )
    # Create the cluster, allowing it to scale
    cluster = KubeCluster(pod_spec)
    cluster.adapt(minimum=1, maximum=10)

    # Set up distributed client
    dask.config.set(
        {"distributed.scheduler.worker-saturation": 1.0}
    )  # Important to prevent root task overloading
    from dask.distributed import Client, as_completed

    client = Client(cluster)
    outputs = [Delayed(x.name, dask_graph) for x in graph.sinks]

    with performance_report(f"{args.output_dir}/performance_report.html"):
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
    logs = cluster._logs()
    await logs
    for pod, pod_log in logs:
        with open(f"{args.output_dir}/{pod.lower()}.log", "w") as logfile:
            logfile.write(pod_log)

    client.close()
    cluster.close()


if __name__ == "__main__":
    main(sys.argv[1:])
