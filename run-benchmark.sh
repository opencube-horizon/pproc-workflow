#!/bin/bash
set -e

source .env
DATE=20231120
CLIM_DATE=20231116
SOURCE=fileset
LOCATION='/home/data/extreme_167.grib'
CLIM_LOCATION=$LOCATION
OUTPUT_DIR=bench_run

for config in configs/*window24.yaml;
    do 
    echo $config
    cp $config config_temp.yaml
    sed -i -e "s/%DATE%/$DATE/g" config_temp.yaml
    sed -i -e "s/%CLIM_DATE%/$CLIM_DATE/g" config_temp.yaml
    sed -i -e "s#%LOCATION%#$LOCATION#g" config_temp.yaml
    sed -i -e "s#%CLIM_LOCATION%#$CLIM_LOCATION#g" config_temp.yaml
    CONFIG_NAME=${config%.*}
    RUN_OUTPUT_DIR=$OUTPUT_DIR/$CONFIG_NAME
    rm -rf $RUN_OUTPUT_DIR
    mkdir -p $RUN_OUTPUT_DIR
    DASK_LOGGING__DISTRIBUTED=debug python scripts/run_benchmark_classic.py --image "docker.io/jinmannwong/pproc-kubernetes:file" --image_secret regcred --output_dir $RUN_OUTPUT_DIR --config config_temp.yaml --ensemble fileset:ens --climatology fileset:clim | tee $RUN_OUTPUT_DIR/console.log
    python scripts/parse_report.py --output_dir $RUN_OUTPUT_DIR  > $RUN_OUTPUT_DIR/results.txt 
    rm config_temp.yaml
done