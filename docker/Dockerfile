# syntax=docker/dockerfile:1.0.0-experimental
FROM ghcr.io/dask/dask:2023.11.0-py3.10

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
RUN --mount=type=ssh git clone ssh://git@git.ecmwf.int/~mawj/pproc-bundle.git -v --branch opencube-benchmark --single-branch --depth 1 
RUN --mount=type=ssh cd /home/pproc-bundle \
    && ./pproc-bundle create \
    && ./pproc-bundle build --without-infero \
    && build/install.sh --fast 

ENV LD_LIBRARY_PATH=/home/pproc-bundle/install/lib:$LD_LIBRARY_PATH
ENV MIR_INCLUDE_DIRS=/home/pproc-bundle/install/include
ENV MIR_LIB_DIR=/home/pproc-bundle/install/lib

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
    git+ssh://git@git.ecmwf.int/ecsdk/pproc.git@1.0.0 \
    git+ssh://git@github.com/ecmwf/cascade.git@92a3a8e \
    git+ssh://git@github.com/ecmwf/pproc-cascade.git@40883a7

RUN --mount=type=ssh git clone ssh://git@git.ecmwf.int/mir/mir-python.git --branch 0.1.0 --single-branch --depth 1 \
    && cd /home/mir-python \
    && python setup.py build_ext \
    && python setup.py install

COPY extreme_167.grib /home/extreme_167.grib