FROM continuumio/miniconda3:4.8.2

WORKDIR /root

RUN apt-get update -qy && apt-get install -qy \
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

ARG CONDA_RC=condarc_student
COPY $CONDA_RC /root/.condarc

ARG CONDA_ENV=conda_lock.yml
COPY $CONDA_ENV /root/conda.yml
RUN conda env update -n base -f conda.yml

# https://github.com/axelfahy/jupyterlab-vim
RUN ($INSTRUCTOR && jupyter labextension install --no-build @axlair/jupyterlab_vim) || true
RUN jupyter labextension install --no-build @jupyterlab/git
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
