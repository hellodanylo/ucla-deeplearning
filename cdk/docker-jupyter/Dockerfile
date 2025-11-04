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
    nvtop \
    procps \
    protobuf-compiler \
    software-properties-common \
    texlive-xetex \
    vim \
    wget \
    unzip \
    zsh \
    >/dev/null 2>&1

RUN conda info

ARG CONDA_ENV=conda_init.yml
COPY cdk/docker-jupyter/$CONDA_ENV ./conda/conda_collegium.yml
COPY cdk/docker-jupyter/conda_collegium_setup.sh ./conda/conda_collegium_setup.sh
RUN ./conda/conda_collegium_setup.sh

# Jupyter Server Proxy for MLFlow
RUN pip install jupyter-server-proxy==4.4.0
COPY cdk/docker-jupyter/jupyter_server_config.py /opt/conda/etc/jupyter/
ENV MLFLOW_TRACKING_URI=file:///home/sagemaker-user/mlflow

COPY --chown=sagemaker-user:sagemaker-user . /app/collegium
WORKDIR /app/collegium

# Nvidia Runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=3

RUN cat - >/opt/conda/lib/python3.12/site-packages/app.pth <<EOF
/app
EOF

ENV XLA_FLAGS=--xla_gpu_cuda_data_dir=/opt/conda
RUN pip install clize==5.0.2 keras_cv==0.9.0
RUN pip install 'transformers<=4.54.1' || true

# Cleanup of unused features
RUN pip uninstall -y amazon_sagemaker_jupyter_ai_q_developer \
    sagemaker-jupyterlab-emr-extension \
    sagemaker_gen_ai_jupyterlab_extension \
    sagemaker-studio-dataengineering-extensions \
    sagemaker-studio-analytics-extension \
    amazon_sagemaker_sql_editor \
    jupyter_ai

RUN jupyter kernelspec uninstall -y glue_pyspark
RUN jupyter kernelspec uninstall -y glue_spark
RUN jupyter kernelspec uninstall -y pysparkkernel
RUN jupyter kernelspec uninstall -y sparkkernel
RUN python -m ipykernel install --sys-prefix --name collegium

COPY cdk/docker-jupyter/install_go.sh /app/install_go.sh
RUN /app/install_go.sh
ENV PATH=/app/go/bin:$PATH

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