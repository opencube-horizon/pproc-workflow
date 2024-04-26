# Setup 

## Dependencies 

Running the benchmark requires the installation of the packages in the ECMWF Github and Bitbucket repositories, not all of which are publicly available. SSH access to these is assumed for the running of the benchmark.

## Build Docker Image

The building of the docker image requires ssh keys to ECMWF's bitbucket and github repositories and these keys should be added using `ssh-add` to the `ssh-agent` key manager. The image also access to ECMWF's MARS client for retrieving the required sample data from the MARS archive. 

To create the sample data file run the `docker/request.sh` script, which will generate the data file `extreme_167.grib` inside the `docker` subdirectory. The docker image can then be built by running 
```
DOCKER_BUILDKIT=1 docker build --ssh default . -t repository:tag --format docker
```

## Kubernetes Permissions

The execution of the task graphs uses the classic Dask KubeCluster, which requires the Kubernetes account to have the following RBAC policy group permissions:
```
- apiGroups:  
    - "policy"  
    resources:  
    - "poddisruptionbudgets"  
    verbs:  
    - "get"
    - "list"
    - "watch"
    - "create"
    - "delete"
```

# Run Benchmark

Assuming access to a Kubernetes Cluster, the benchmark can be run by executing the `run-benchmark.sh` script, which will build and install the required dependencies.

# License

All code is under the Apache 2 license.
