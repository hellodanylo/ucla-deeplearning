FROM ghcr.io/hellodanylo/humus:main

WORKDIR /root

ARG CONDA_VERSION=Miniconda3-py39_4.12.0-Linux-x86_64
RUN wget -q -O conda_install.sh "https://repo.anaconda.com/miniconda/$CONDA_VERSION.sh"
RUN bash conda_install.sh -b
RUN rm conda_install.sh

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -q && apt-get install -qy \
    procps \
    htop \
    zip \
    unzip \
    vim \
    gnupg \
    texlive-xetex \
    software-properties-common \
    protobuf-compiler \
    build-essential \
    >/dev/null 2>&1

ENV PATH="/root/miniconda3/bin:$PATH"

ARG CONDA_RC=condarc_default.yml
COPY $CONDA_RC /root/.condarc

RUN conda info

ARG CONDA_JUPYTER_ENV=conda_jupyter_lock.yml
COPY $CONDA_JUPYTER_ENV /root/conda_jupyter.yml
RUN conda env create -n jupyter -f conda_jupyter.yml
ENV PATH="/root/miniconda3/envs/jupyter/bin:$PATH"

# https://github.com/axelfahy/jupyterlab-vim
ARG VIM=false
RUN ($VIM && pip install jupyterlab-vim)

ARG CONDA_DEEPLEARNING_ENV=conda_deeplearning_lock.yml
COPY $CONDA_DEEPLEARNING_ENV /root/conda_deeplearning.yml
ENV CONDA_OVERRIDE_CUDA="11.2"
RUN conda env create -n ucla_deeplearning -f conda_deeplearning.yml
RUN /root/miniconda3/envs/ucla_deeplearning/bin/ipython kernel install --user --name=ucla_deeplearning

RUN conda init zsh
ENV SHELL=/bin/zsh
WORKDIR /app

# Nvidia Runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV NVIDIA_REQUIRE_CUDA="cuda>=10.0 brand=tesla,driver>=384,driver<385 brand=tesla,driver>=410,driver<411"

CMD jupyter \
    lab \
    --notebook-dir=/app \
    --ip=0.0.0.0 \
    --port=80 \
    --no-browser \
    --allow-root
