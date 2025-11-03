ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG TZ=America/Los_Angeles
RUN sudo ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
RUN echo $TZ | sudo tee -a /etc/timezone

RUN sudo apt-get update -q && \
    sudo apt-get install -qy \
    build-essential \
    exa \
    ffmpeg \
    gnupg \
    htop \
    jq \
    procps \
    protobuf-compiler \
    software-properties-common \
    texlive-xetex \
    zsh \
    >/dev/null 2>&1

RUN conda info

ARG CONDA_ENV=conda_init.yml
COPY cdk/docker-jupyter/$CONDA_ENV ./conda/conda_collegium.yml
COPY cdk/docker-jupyter/conda_collegium_setup.sh ./conda/conda_collegium_setup.sh
RUN ./conda/conda_collegium_setup.sh
# ENV PATH="/app/conda/envs/collegium/bin:$PATH"

# Jupyter Server Proxy for MLFlow
# RUN conda run -n jupyter pip install jupyter-server-proxy==4.0.0
# COPY cdk/docker-jupyter/jupyter_server_config.py /app/conda/envs/jupyter/etc/jupyter/
# COPY cdk/docker-jupyter/mlflow.svg /app/conda/envs/jupyter/mlflow.svg
# ENV MLFLOW_TRACKING_URI=file:///app/mlflow

COPY --chown=sagemaker-user:sagemaker-user . /app/collegium
WORKDIR /app/collegium

# Nvidia Runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
# ENV NVIDIA_REQUIRE_CUDA="cuda>=10.0 brand=tesla,driver>=384,driver<385 brand=tesla,driver>=410,driver<411"
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=3

RUN cat - >/opt/conda/lib/python3.12/site-packages/app.pth <<EOF
/app
EOF

ENV XLA_FLAGS=--xla_gpu_cuda_data_dir=/opt/conda
RUN pip install clize

RUN jupyter kernelspec uninstall -y glue_pyspark
RUN jupyter kernelspec uninstall -y glue_spark
RUN jupyter kernelspec uninstall -y pysparkkernel
RUN jupyter kernelspec uninstall -y sparkkernel
RUN python -m ipykernel install --sys-prefix --name collegium

CMD jupyter \
    lab \
    --notebook-dir=/home/sagemaker-user \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --allow-root \
    --ServerApp.base_url="/jupyterlab/default" \
    --ServerApp.token='' \
    --ServerApp.allow_origin='*'