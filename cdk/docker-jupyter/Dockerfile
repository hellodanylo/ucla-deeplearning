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
    ffmpeg \
    >/dev/null 2>&1

RUN conda info

ARG CONDA_ENV=conda_lock.yml
COPY cdk/docker-jupyter/$CONDA_ENV ./conda/conda_collegium.yml
COPY cdk/docker-jupyter/conda_collegium_setup.sh ./conda/conda_collegium_setup.sh
RUN ./conda/conda_collegium_setup.sh
ENV PATH="/app/conda/envs/collegium/bin:$PATH"

# Jupyter Server Proxy for MLFlow
RUN conda run -n jupyter pip install jupyter-server-proxy==4.0.0
COPY cdk/docker-jupyter/jupyter_server_config.py /app/conda/envs/jupyter/etc/jupyter/
COPY cdk/docker-jupyter/mlflow.svg /app/conda/envs/jupyter/mlflow.svg
ENV MLFLOW_TRACKING_URI=file:///app/mlflow

COPY --chown=user:user . /app/collegium
WORKDIR /app/collegium

# Nvidia Runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV NVIDIA_REQUIRE_CUDA="cuda>=10.0 brand=tesla,driver>=384,driver<385 brand=tesla,driver>=410,driver<411"
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=3

CMD /app/conda/envs/jupyter/bin/jupyter \
    lab \
    --notebook-dir=/app \
    --ip=0.0.0.0 \
    --port=80 \
    --no-browser \
    --allow-root
