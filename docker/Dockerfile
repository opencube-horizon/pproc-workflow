FROM ghcr.io/opencube-horizon/pproc-dask:fdb-fam

WORKDIR /tmp/build

ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH
ENV MIR_INCLUDE_DIRS=/usr/local/include
ENV MIR_LIB_DIR=/usr/local/lib64
COPY meteokit /tmp/build/meteokit

RUN pip install \
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
    /tmp/build/meteokit \
    git+https://github.com/ecmwf/pyfdb.git@0.0.3 \
    git+https://github.com/ecmwf/pproc.git@1.1.0 \
    git+https://github.com/ecmwf/earthkit-workflows.git@92a3a8e \
    git+https://github.com/ecmwf/earthkit-workflows-pproc.git@40883a7


RUN git clone https://github.com/ecmwf/mir-python.git --branch 0.2.0 --single-branch --depth 1 \
    && cd mir-python \
    && python setup.py build_ext \
    && python setup.py install

RUN rm -rf /tmp/build

WORKDIR /home/benchmark
RUN groupadd -g 20013 ecmwf 
 
COPY templates/remote-config.yaml /home/benchmark/fdb/remote/etc/fdb/config.yaml
COPY templates/local-config.yaml /home/benchmark/fdb/local/etc/fdb/config.yaml
COPY templates/fam-schema /home/benchmark/fdb/local/etc/fdb/schema
COPY configure_fdb.sh /home/benchmark/configure_fdb.sh
RUN sed -i "s;%SCHEMA%;/home/benchmark/fdb/local/etc/fdb/schema;g" /home/benchmark/fdb/local/etc/fdb/config.yaml
RUN chgrp --recursive ecmwf /home/benchmark && chmod --recursive g=u /home/benchmark

RUN useradd -M -d /home/benchmark -u 1234 -g 20013 benchuser
USER benchuser
ENV USER=benchuser
ENV HOME=/home/benchmark
WORKDIR /home/benchmark

ENV FINDLIBS_DISABLE_PACKAGE=yes
ENTRYPOINT ["tini", "-g", "--", "/home/benchmark/configure_fdb.sh"]
