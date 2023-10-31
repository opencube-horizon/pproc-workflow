# Setup 

## Dependencies 

Running the benchmark requires the installation of the packages in https://git.ecmwf.int/projects/ECSDK/repos/pproc-bundle, and mir-python https://git.ecmwf.int/projects/MIR/repos/mir-python, which requires cython. The remaining Python dependencies are specified in the requirements.txt file.


## FDB

The benchmark requires a remote FDB to be running where the host and port must be configured correctly in docker/fdb/config.yaml for the docker image to be set up to use the remote FDB. The schema in docker/fdb/schema must also match that of the remote FDB.

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

