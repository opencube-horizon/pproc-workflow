#!/bin/bash
set -e


# Activate environment and load dependencies
ARCH=$(uname -m)
source /home/jwong/venvs/$ARCH/pproc_env/bin/activate

BUNDLE_PATH=/home/jwong/pproc-bundles/$ARCH/fam/pproc-bundle

if [ ! -e $BUNDLE_PATH ];
then 
   echo "Bundle $BUNDLE_PATH does not exist. Exiting"
   exit 1
fi

export FINDLIBS_DISABLE_PACKAGE=yes
export LD_LIBRARY_PATH=$BUNDLE_PATH/install/lib64:$LD_LIBRARY_PATH
echo $LD_LIBRARY_PATH

# Run benchmark
DATE=20260107
CLIM_DATE=20260105
SOURCE=fdb
TARGET=fdb:
OUTPUT_DIR=bench_run
IMAGE=ghcr.io/opencube-horizon/pproc-benchmark@sha256:620659c139364fcddce10160c690c6123b0f71f9ca3ba1bcc6815dc2d7466f4f
SECRET=git-dask
NODES="cn05 cn06 cn07"

LATEST_RUN_NUMBER=$(ls $OUTPUT_DIR | tail -1)
NEXT_RUN_NUMBER=$(printf "%06d" "$(expr $LATEST_RUN_NUMBER + 1)")
RUN_DIR=$OUTPUT_DIR/$NEXT_RUN_NUMBER
mkdir -p $RUN_DIR

FDB_TYPE=${1:-local}
if [ $FDB_TYPE = "remote" ]; then
   cat > $RUN_DIR/fdb_options.yaml << EOF
FDB_TYPE: remote
FDB_HOST: ${2:-"infra2"}
FDB_PORT: ${3:-"9000"}
EOF
elif [ $FDB_TYPE = "local" ]; then
  cat > $RUN_DIR/fdb_options.yaml << EOF
FDB_HOST_INDEX: ${2:-"/shared/scratch/ECMWF/D5.2/fam/database"}
FDB_TYPE: local
FDB_INDEX: ${3:-"/home/fdb/local/data"}
FDB_FAM_URI: ${4:-"fam://10.115.3.2:8080/jw_data_region"}
EOF
fi

cat > $RUN_DIR/run_options.txt << EOF
SOURCE=$SOURCE
TARGET=$TARGET
IMAGE=$IMAGE
LOCAL=$LOCAL
NODES=$NODES
EOF

export KUBECONFIG=$(realpath /home/jwong/.kube/config)

for config in configs/extreme_2t.yaml;
    do 
    echo $config
    cp $config config_temp.yaml
    sed -i -e "s/%DATE%/$DATE/g" config_temp.yaml
    sed -i -e "s/%CLIM_DATE%/$CLIM_DATE/g" config_temp.yaml
    sed -i -e "s#%TARGET%#$TARGET#g" config_temp.yaml
    CONFIG_NAME=$(basename ${config%.*})
    RUN_OUTPUT_DIR=$RUN_DIR/$CONFIG_NAME
    echo $RUN_OUTPUT_DIR
    rm -rf $RUN_OUTPUT_DIR
    mkdir -p $RUN_OUTPUT_DIR
    cp config_temp.yaml $RUN_OUTPUT_DIR/config.yaml
    DASK_LOGGING__DISTRIBUTED=debug python scripts/run_benchmark_classic.py $LOCAL --image $IMAGE --image_secret $SECRET --node-list $NODES --output_dir $RUN_OUTPUT_DIR --config config_temp.yaml --ensemble $SOURCE:ens --climatology $SOURCE:clim --fdb-options $RUN_DIR/fdb_options.yaml | tee $RUN_OUTPUT_DIR/console.log
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
