# syntax=docker/dockerfile:1.0.0-experimental
FROM ghcr.io/opencube-horizon/pproc-dask:fdb-fam

WORKDIR /tmp/build
RUN git clone https://github.com/ecmwf/ecbuild
RUN git clone https://github.com/ecmwf/mir.git -v --branch develop --single-branch

ENV PATH=/usr/local/bin:$PATH

RUN export CC=gcc-12 && export CXX=g++-12 && cd mir \
    && git checkout 5cd2929afb2f333e46d5e45124cd0cf6da36445c \
    && mkdir build \
    && cd build \
    && /tmp/build/ecbuild/bin/ecbuild .. -G Ninja -DCMAKE_BUILD_TYPE=BIT -DCMAKE_INSTALL_PREFIX=/usr/local -DENABLE_TESTS=OFF -DENABLE_ATLAS=OFF -DENABLE_MIR_DOWNLOAD_MASKS=OFF \
    && ninja -j12 \
    && cmake --install . 

RUN mkdir -p -m 0600 /root/.ssh \
    && ssh-keyscan git.ecmwf.int >> /root/.ssh/known_hosts \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts \
    && cat /root/.ssh/known_hosts

ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH
ENV MIR_INCLUDE_DIRS=/usr/local/include
ENV MIR_LIB_DIR=/usr/local/lib64

RUN --mount=type=ssh pip install \
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
    git+ssh://git@git.ecmwf.int/ecsdk/meteokit.git@0.1.0 \
    git+https://github.com/ecmwf/pyfdb.git@0.0.3 \
    git+https://github.com/ecmwf/pproc.git@1.1.0 \
    git+https://github.com/ecmwf/earthkit-workflows.git@92a3a8e \
    git+https://github.com/ecmwf/earthkit-workflows-pproc.git@40883a7


RUN --mount=type=ssh git clone ssh://git@git.ecmwf.int/mir/mir-python.git --branch 0.2.0 --single-branch --depth 1 \
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