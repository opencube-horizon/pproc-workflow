#!/usr/bin/env bash

basewd=$PWD

rm -f build.done build.fail

handle_error() {
  set +e
  touch $basewd/build.fail
  trap 0
  exit 1
}
trap handle_error ERR

set -e

# Build binary packages
mkdir -p build
cd build
if [[ ! -e pproc-bundle ]]; then 
  git clone ssh://git@git.ecmwf.int/~mawj/pproc-bundle.git -v --branch opencube-benchmark --single-branch --depth 1 
fi
cd pproc-bundle 
./pproc-bundle create 
./pproc-bundle build --without-infero 
build/install.sh --fast 
cd ../..
BUNDLE_PATH=$(realpath build/pproc-bundle)

export LD_LIBRARY_PATH=$BUNDLE_PATH/install/lib64:$LD_LIBRARY_PATH
export MIR_INCLUDE_DIRS=$BUNDLE_PATH/install/include
export MIR_LIB_DIR=$BUNDLE_PATH/install/lib64

rm -rf env
python3.11 -m venv env
source env/bin/activate
python -m pip install -r requirements.txt
    
cd build
git clone ssh://git@git.ecmwf.int/mir/mir-python.git --branch 0.2.0 --single-branch --depth 1 
cd mir-python 
python setup.py build_ext 
python setup.py install

deactivate

touch $basewd/build.done
