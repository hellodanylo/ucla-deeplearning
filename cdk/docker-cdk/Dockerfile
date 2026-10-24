# Deployment tooling image: CDK app (cdk/pyproject.toml), CDK CLI and SageMaker job launcher (cdk/cli.py).
# Used by cdk/cdk_deploy.sh and cdk/test_sagemaker.sh; the Studio image is cdk/docker-studio/Dockerfile.
FROM public.ecr.aws/docker/library/ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -q && \
    apt-get install -qy --no-install-recommends ca-certificates git tzdata >/dev/null && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/
ENV UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1

# Only the project files are copied before syncing, so this layer is cached across code changes;
# the `collegium` package itself is made importable via app.pth instead of an editable install.
ARG CDK_VERSION=2.1031.1
COPY pyproject.toml /app/collegium/pyproject.toml
COPY cdk/pyproject.toml cdk/uv.lock /app/collegium/cdk/
RUN cd /app/collegium/cdk && \
    uv python install 3.12 && \
    uv sync --frozen --no-cache --no-install-package collegium && \
    echo /app > /opt/venv/lib/python3.12/site-packages/app.pth && \
    npm install -g --prefix /opt/venv aws-cdk@${CDK_VERSION}

COPY . /app/collegium
WORKDIR /app/collegium/cdk
