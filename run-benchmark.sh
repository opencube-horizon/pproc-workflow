source .env

OUTPUT_DIR=bench_run

for config in configs/*.yaml;
    do 
    echo config
    CONFIG_NAME=${config%.*}
    RUN_OUTPUT_DIR=$OUTPUT_DIR/$CONFIG_NAME
    mkdir -p $RUN_OUTPUT_DIR
    python scripts/run_benchmark_classic.py --image "docker.io/jinmannwong/pproc-kubernetes:latest" --secret regcred --output_dir $RUN_OUTPUT_DIR --graph_config config > $RUN_OUTPUT_DIR/console.log
    python scripts/parse_report.py --output_dir $RUN_OUTPUT_DIR > $RUN_OUTPUT_DIR/results.txt
done