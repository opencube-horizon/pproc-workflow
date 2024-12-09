#!/bin/bash
set -e


# Activate environment and load dependencies
ARCH=$(uname -m)
source /home/jwong/venvs/$ARCH/pproc_env/bin/activate
ENABLE_FAM=${1:-0}
if [ $ENABLE_FAM == 0 ];
then 
    BUNDLE_DIR=default
else
    export OPENFAM_ROOT="/shared/members/ECMWF/software/fam/$ARCH"
    export LD_LIBRARY_PATH="/opt/cray/libfabric/1.20.1/lib64:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="/shared/WP/3/OpenFam/$ARCH/install/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="/shared/WP/3/OpenFam/$ARCH/install/lib64:$LD_LIBRARY_PATH"
    BUNDLE_DIR=fam
fi
BUNDLE_PATH=/home/jwong/pproc-bundles/$ARCH/$BUNDLE_DIR/pproc-bundle

if [ ! -e $BUNDLE_PATH ];
then 
   echo "Bundle $BUNDLE_PATH does not exist. Exiting"
   exit 1
fi

export LD_LIBRARY_PATH=$BUNDLE_PATH/install/lib64:$LD_LIBRARY_PATH
echo $LD_LIBRARY_PATH

# Run benchmark
DATE=20231122
CLIM_DATE=20231120
SOURCE=fdb #fileset
TARGET=fdb: #fileset:cascade_extreme_{param}.grib
LOCATION='/home/extreme_167.grib'
CLIM_LOCATION=$LOCATION
OUTPUT_DIR=bench_run
IMAGE=ghcr.io/opencube-horizon/pproc-benchmark@sha256:dab2b5e57f2b7f6262a5908e7277478a6c3ef4a4b8bd8c0cfae8b6672889ba56
SECRET=github
LOCAL=""
if [ "$LOCAL" == "" ]; then
   export FDB_HOST=cn03
   export FDB_PORT=9000
fi

LATEST_RUN_NUMBER=$(ls $OUTPUT_DIR | tail -1)
NEXT_RUN_NUMBER=$(printf "%06d" "$(expr $LATEST_RUN_NUMBER + 1)")
mkdir $OUTPUT_DIR/$NEXT_RUN_NUMBER
cat > $OUTPUT_DIR/$NEXT_RUN_NUMBER/run_options.txt << EOF
SOURCE=$SOURCE
TARGET=$TARGET
IMAGE=$IMAGE
LOCAL=$LOCAL
FDB_HOST=${FDB_HOST:-""}
FDB_PORT=${FDB_PORT:-""}
EOF

for config in configs/*.yaml;
    do 
    echo $config
    cp $config config_temp.yaml
    sed -i -e "s/%DATE%/$DATE/g" config_temp.yaml
    sed -i -e "s/%CLIM_DATE%/$CLIM_DATE/g" config_temp.yaml
    sed -i -e "s#%LOCATION%#$LOCATION#g" config_temp.yaml
    sed -i -e "s#%CLIM_LOCATION%#$CLIM_LOCATION#g" config_temp.yaml
    sed -i -e "s#%TARGET%#$TARGET#g" config_temp.yaml
    CONFIG_NAME=$(basename ${config%.*})
    RUN_OUTPUT_DIR=$OUTPUT_DIR/$NEXT_RUN_NUMBER/$CONFIG_NAME
    echo $RUN_OUTPUT_DIR
    rm -rf $RUN_OUTPUT_DIR
    mkdir -p $RUN_OUTPUT_DIR
    cp config_temp.yaml $RUN_OUTPUT_DIR/config.yaml
    DASK_LOGGING__DISTRIBUTED=debug python scripts/run_benchmark_classic.py $LOCAL --image $IMAGE --image_secret $SECRET --output_dir $RUN_OUTPUT_DIR --config config_temp.yaml --ensemble $SOURCE:ens --climatology $SOURCE:clim | tee $RUN_OUTPUT_DIR/console.log
    if [ "$LOCAL" == "" ]; then 
        for worker_log in $RUN_OUTPUT_DIR/worker*.log;
        do 
            cat $worker_log >> $RUN_OUTPUT_DIR/console.log
        done 
    fi
    python scripts/parse_report.py --output_dir $RUN_OUTPUT_DIR  > $RUN_OUTPUT_DIR/results.txt 
    rm config_temp.yaml
done
deactivate
