#!/bin/bash

TYPE=${FDB_TYPE}

# Set up FDB config
if [ "$TYPE" = "remote" ]; then 
    export FDB_HOME=/home/benchmark/fdb/remote
    HOST=${FDB_HOST}
    PORT=${FDB_PORT}
    echo "ARGS:" $TYPE $HOST $PORT
    sed -i "s/%HOST%/$HOST/g" ${FDB_HOME}/etc/fdb/config.yaml
    sed -i "s/%PORT%/$PORT/g" ${FDB_HOME}/etc/fdb/config.yaml
elif [ "$TYPE" = "local" ]; then 
    export FDB_HOME=/home/benchmark/fdb/local
    INDEX=${FDB_INDEX}
    FAM_URI=${FDB_FAM_URI}
    echo "ARGS:" $TYPE $INDEX $FAM_URI
    sed -i "s;%INDEX%;$INDEX;g" ${FDB_HOME}/etc/fdb/config.yaml
    sed -i "s;%FAM_URI%;${FAM_URI};g" ${FDB_HOME}/etc/fdb/config.yaml
else
    echo "Unknown FDB type $TYPE"
    exit 1
fi

cat ${FDB_HOME}/etc/fdb/config.yaml

# Run extra commands
exec "$@"