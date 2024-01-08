#!/bin/bash
set -e

source .env

DATE=20231122
CLIM_DATE=20231120
SOURCE=fileset
LOCATION='/home/extreme_167.grib'
CLIM_LOCATION=$LOCATION
OUTPUT_DIR=bench_run
LOCAL=""

LATEST_RUN_NUMBER=$(ls $OUTPUT_DIR | tail -1)
NEXT_RUN_NUMBER=$(printf "%06d" "$((LATEST_RUN_NUMBER + 1))")

for config in configs/*.yaml;
    do 
    echo $config
    cp $config config_temp.yaml
    sed -i -e "s/%DATE%/$DATE/g" config_temp.yaml
    sed -i -e "s/%CLIM_DATE%/$CLIM_DATE/g" config_temp.yaml
    sed -i -e "s#%LOCATION%#$LOCATION#g" config_temp.yaml
    sed -i -e "s#%CLIM_LOCATION%#$CLIM_LOCATION#g" config_temp.yaml
    CONFIG_NAME=$(basename ${config%.*})
    RUN_OUTPUT_DIR=$OUTPUT_DIR/$NEXT_RUN_NUMBER/$CONFIG_NAME
    echo $RUN_OUTPUT_DIR
    rm -rf $RUN_OUTPUT_DIR
    mkdir -p $RUN_OUTPUT_DIR
    DASK_LOGGING__DISTRIBUTED=debug python scripts/run_benchmark_classic.py $LOCAL --image "docker.io/jinmannwong/pproc-kubernetes:file" --image_secret regcred --output_dir $RUN_OUTPUT_DIR --config config_temp.yaml --ensemble $SOURCE:ens --climatology $SOURCE:clim | tee $RUN_OUTPUT_DIR/console.log
    if [ "$LOCAL" == "" ]; then 
        for worker_log in $RUN_OUTPUT_DIR/worker*.log;
        do 
            cat $worker_log >> $RUN_OUTPUT_DIR/console.log
        done 
    fi
    python scripts/parse_report.py --output_dir $RUN_OUTPUT_DIR  > $RUN_OUTPUT_DIR/results.txt 
    rm config_temp.yaml
done