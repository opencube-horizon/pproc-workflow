FROM ghcr.io/opencube-horizon/pproc-dask:fdb-fam

WORKDIR /tmp/build

ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH
ENV MIR_INCLUDE_DIRS=/usr/local/include
ENV MIR_LIB_DIR=/usr/local/lib64
ENV ECCODES_PYTHON_USE_FINDLIBS=1
ENV FINDLIBS_DISABLE_PACKAGE=yes
COPY meteokit /tmp/build/meteokit

RUN source /home/env/bin/activate \ 
    && python -m pip install \
    cython==3.0.8 \
    eccodes==1.6.1 \
    earthkit-data==0.4.0 \
    "filelock>=3.12.0" \
    numexpr==2.8.8 \
    dill==0.3.7 \
    sortedcontainers \
    scipy==1.11.4 \
    array_api_compat==1.4 \
    pyvis==0.3.2 \
    bokeh==3.3.3 \
    findlibs==0.1.2 \
    "setuptools<82" \
    /tmp/build/meteokit \
    pyfdb==0.1.1 \
    git+https://github.com/ecmwf/pproc.git@1.1.0 \
    git+https://github.com/ecmwf/earthkit-workflows.git@92a3a8e \
    git+https://github.com/ecmwf/earthkit-workflows-pproc.git@40883a7


RUN export CC=gcc-15 \
    && export CXX=g++-15 \
    && git clone https://github.com/ecmwf/mir-python.git --branch 0.2.0 --single-branch --depth 1 \
    && cd mir-python \
    && source /home/env/bin/activate \
    && python setup.py build_ext \
    && python setup.py install

RUN rm -rf /tmp/build

WORKDIR /home/benchmark
 
COPY templates/remote-config.yaml /home/benchmark/fdb/remote/etc/fdb/config.yaml
COPY templates/local-config.yaml /home/benchmark/fdb/local/etc/fdb/config.yaml
COPY templates/fam-schema /home/benchmark/fdb/local/etc/fdb/schema
COPY configure_fdb.sh /home/benchmark/configure_fdb.sh
RUN sed -i "s;%SCHEMA%;/home/benchmark/fdb/local/etc/fdb/schema;g" /home/benchmark/fdb/local/etc/fdb/config.yaml

ENV HOME=/home/benchmark
WORKDIR /home/benchmark

ENTRYPOINT ["tini", "-g", "--", "/home/benchmark/configure_fdb.sh"]
