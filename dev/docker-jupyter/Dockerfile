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

ARG CONDA_RC=condarc_default
COPY $CONDA_RC /root/.condarc

ARG CONDA_ENV=conda_lock.yml
COPY $CONDA_ENV /root/conda.yml
RUN conda env create -n ucla_deeplearning -f conda.yml
RUN conda init zsh
RUN conda shell.zsh activate jupyter >>/root/.zshenv

# https://github.com/axelfahy/jupyterlab-vim
ARG VIM=false
RUN ($VIM && jupyter labextension install --no-build @axlair/jupyterlab_vim@0.12.4) || true
RUN jupyter labextension install --no-build @jupyterlab/git@0.21.1
RUN jupyter serverextension enable --py jupyterlab_git --sys-prefix >/dev/null
RUN jupyter lab build

# Nvidia Runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV NVIDIA_REQUIRE_CUDA="cuda>=10.0 brand=tesla,driver>=384,driver<385 brand=tesla,driver>=410,driver<411"

RUN ln -s /root/.ssh/gitconfig /root/.gitconfig

CMD /opt/conda/bin/jupyter \
    lab \
    --notebook-dir=/app \
    --ip=0.0.0.0 \
    --port=80 \
    --no-browser \
    --allow-root
