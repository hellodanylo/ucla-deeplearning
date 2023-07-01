ARG BASE_IMAGE
FROM ${BASE_IMAGE}

RUN sudo ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
RUN echo $TZ | sudo tee -a /etc/timezone

RUN sudo apt-get update -q && \
    sudo apt-get install -qy \
    procps \
    htop \
    gnupg \
    texlive-xetex \
    software-properties-common \
    protobuf-compiler \
    build-essential \
    >/dev/null 2>&1

RUN conda info

ARG CONDA_ENV=conda_lock.yml
COPY cdk/docker-jupyter/$CONDA_ENV ./conda_deeplearning.yml
ENV CONDA_OVERRIDE_CUDA="11.2"
RUN conda env create -n collegium -f ./conda_deeplearning.yml
RUN /app/miniconda/envs/collegium/bin/ipython kernel install --user --name=collegium
RUN conda run -n collegium npm -g install aws-cdk@2.86.0
ENV PATH="/app/miniconda/envs/collegium/bin:$PATH"

RUN conda init zsh
WORKDIR /app

# Git complains about ownership by another user (this image runs as root)
USER user:user
COPY --chown=user:user . /app/collegium
RUN git config --global --add safe.directory /app/collegium

# Nvidia Runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV NVIDIA_REQUIRE_CUDA="cuda>=10.0 brand=tesla,driver>=384,driver<385 brand=tesla,driver>=410,driver<411"

CMD jupyter \
    lab \
    --notebook-dir=/app/ucla-deeplearning \
    --ip=0.0.0.0 \
    --port=80 \
    --no-browser \
    --allow-root
