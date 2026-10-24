# SageMaker Studio JupyterLab image without SageMaker Distribution or conda.
# CUDA comes from the tensorflow[and-cuda] wheels; the driver is mounted by the host's NVIDIA runtime.
# Studio requirements: https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-byoi-specs.html
FROM public.ecr.aws/docker/library/ubuntu:24.04

ARG NB_USER=sagemaker-user
ARG NB_UID=1000
ARG NB_GID=100
ARG TZ=America/Los_Angeles

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -q && \
    apt-get install -qy --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    ffmpeg \
    git \
    gnupg \
    htop \
    jq \
    less \
    nvtop \
    pandoc \
    procps \
    protobuf-compiler \
    sudo \
    texlive-fonts-recommended \
    texlive-plain-generic \
    texlive-xetex \
    tzdata \
    unzip \
    vim \
    wget \
    zsh \
    >/dev/null && \
    rm -rf /var/lib/apt/lists/*

# AWS CLI v2: notebooks download datasets with `aws s3 cp`
ARG AWSCLI_VERSION=2.38.1
RUN curl -sSL -o /tmp/awscli.zip https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWSCLI_VERSION}.zip && \
    unzip -q /tmp/awscli.zip -d /tmp && /tmp/aws/install && rm -rf /tmp/aws /tmp/awscli.zip

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Ubuntu images ship an `ubuntu` user with UID 1000, which Studio requires for its own user
RUN userdel -r ubuntu && \
    useradd --create-home --shell /bin/bash --uid $NB_UID --gid $NB_GID $NB_USER && \
    echo "$NB_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$NB_USER

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/
ENV UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH
RUN install -d -o $NB_USER -g $NB_GID /opt/python /opt/venv /app

USER $NB_USER
COPY --chown=$NB_USER:$NB_GID cdk/docker-studio/pyproject.toml cdk/docker-studio/uv.lock /app/collegium/cdk/docker-studio/
RUN cd /app/collegium/cdk/docker-studio && \
    uv python install 3.12 && \
    uv sync --frozen --no-cache && \
    echo /app > /opt/venv/lib/python3.12/site-packages/app.pth && \
    python -m ipykernel install --sys-prefix --name collegium --display-name collegium

# The tensorflow 2.21 wheel dlopens libcusolver from a library whose RUNPATH lacks nvidia/cusolver/lib.
# An ld.so.conf.d entry is not enough: SageMaker's NVIDIA runtime hook regenerates ld.so.cache without it.
ENV LD_LIBRARY_PATH=/opt/venv/lib/python3.12/site-packages/nvidia/cusolver/lib

COPY --chown=$NB_USER:$NB_GID cdk/docker-studio/triton_deepbind.py /opt/venv/lib/python3.12/site-packages/
RUN echo "import triton_deepbind" > /opt/venv/lib/python3.12/site-packages/triton_deepbind.pth

COPY --chown=$NB_USER:$NB_GID cdk/docker-studio/jupyter_server_config.py /opt/venv/etc/jupyter/jupyter_server_config.py
COPY --chown=$NB_USER:$NB_GID . /app/collegium

ENV SHELL=/bin/bash \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=3 \
    # MLflow 3 no longer accepts the file store; sqlite creates ~/mlflow on first use
    MLFLOW_TRACKING_URI=sqlite:////home/sagemaker-user/mlflow/mlflow.db \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

WORKDIR /home/$NB_USER
CMD jupyter lab \
    --notebook-dir=/home/sagemaker-user \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --ServerApp.base_url="/jupyterlab/default" \
    --ServerApp.token='' \
    --ServerApp.allow_origin='*'
