# syntax=docker/dockerfile:1.0.0-experimental
FROM ghcr.io/dask/dask:latest-py3.10

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && apt-get install -y gnupg

# get intel key
RUN wget https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
    && apt-key add GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    intel-mkl \
    libopenblas-dev \
    libaec-dev \
    git \
    openmpi-bin \
    libopenmpi-dev \
    gfortran \
    curl \
    flex \
    bison

ENV CMAKE_LIBRARY_PATH=$CMAKE_LIBRARY_PATH:/usr/lib/x86_64-linux-gnu
ENV CMAKE_INCLUDE_PATH=$CMAKE_INCLUDE_PATH:/usr/include/mkl

# install fftw
ADD http://www.fftw.org/fftw-3.3.9.tar.gz /fftw-3.3.9.tar.gz
RUN tar -xzf /fftw-3.3.9.tar.gz \
    && cd fftw-3.3.9 \
    && ./configure --enable-type-prefix \
            --prefix=/usr \
            --enable-shared  \
            --disable-static \
            --enable-threads \
            --enable-sse2    \
            --enable-avx \
    && make \
    && make install \ 
    && make clean \
    && ./configure --enable-float \
            --enable-type-prefix \
            --prefix=/usr \
            --enable-shared  \
            --disable-static \
            --enable-threads \
            --enable-sse2    \
            --enable-avx \
    && make \
    && make install

WORKDIR /home
RUN mkdir -p -m 0600 /root/.ssh \
    && ssh-keyscan git.ecmwf.int >> /root/.ssh/known_hosts \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts \
    && cat /root/.ssh/known_hosts

# pproc-bundle
RUN --mount=type=ssh git clone ssh://git@git.ecmwf.int/ecsdk/pproc-bundle.git -v --branch master --single-branch --depth 1 
RUN --mount=type=ssh cd /home/pproc-bundle \
    && ./pproc-bundle create \
    && ./pproc-bundle build --without-infero \
    && build/install.sh --fast 

ENV LD_LIBRARY_PATH=/home/pproc-bundle/install/lib:$LD_LIBRARY_PATH
ENV MIR_INCLUDE_DIRS=/home/pproc-bundle/install/include
ENV MIR_LIB_DIR=/home/pproc-bundle/install/lib

RUN --mount=type=ssh pip install cython

RUN --mount=type=ssh git clone ssh://git@git.ecmwf.int/mir/mir-python.git --branch master --single-branch --depth 1 \
    && cd /home/mir-python \
    && python setup.py build_ext \
    && python setup.py install

RUN --mount=type=ssh pip install git+ssh://git@github.com/ecmwf/cascade.git 

# Configure FDB
ENV FDB_HANDLE_LUSTRE_STRIPE=0
ENV FDB_HOME=/home/config/fdb
RUN mkdir -p /home/config
COPY fdb /home/config/fdb
RUN cat /home/config/fdb/config.yaml \
    && /home/pproc-bundle/install/bin/fdb info --all

RUN mkdir -p /home/data
COPY extreme_167.grib /home/data/extreme_167.grib