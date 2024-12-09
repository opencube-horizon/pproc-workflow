#!/bin/bash

HOST=${FDB_HOST:-infra1}
PORT=${FDB_PORT:-9000}

echo "ARGS:" $HOST $PORT 

# Set up FDB config
sed -i "s/%HOST%/$HOST/g" /home/fdb/etc/fdb/config.yaml
sed -i "s/%PORT%/$PORT/g" /home/fdb/etc/fdb/config.yaml

# Run extra commands
exec "$@"