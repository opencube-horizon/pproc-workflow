# Setup 

## Dependencies 

Running the benchmark requires the installation of the packages in the ECMWF Github and Bitbucket repositories, not all of which are publicly available. SSH access to these is assumed for the running of the benchmark.

## Build Docker Image

The building of the docker image requires ssh keys to ECMWF's bitbucket and github repositories to be set up. The ssh-agent should then be started and these keys should be added to the agent. The docker image can then be built by running 
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

The benchmark can be run by executing the `run-benchmark.sh` script, which will build and install the required dependencies.

