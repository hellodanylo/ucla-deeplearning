# Deployment tooling image: CDK app (cdk/pyproject.toml), CDK CLI, SageMaker job launcher (cdk/cli.py) and the Go
# admin tools (cdk/welcome_team; `docker run ... welcome_team [user ...]` emails credentials — run deliberately).
# Used by cdk/cdk_deploy.sh and cdk/test_sagemaker.sh; the Studio image is cdk/docker-studio/Dockerfile.
FROM public.ecr.aws/docker/library/ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -q && \
    apt-get install -qy --no-install-recommends ca-certificates curl git tzdata >/dev/null && \
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

# Go toolchain for cdk/go.mod, pinned and checksum-verified; GOTOOLCHAIN=local stops it fetching other versions
ARG GO_VERSION=1.27.3
ARG GO_SHA256=65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40
RUN curl -fsSL -o /tmp/go.tgz https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    echo "${GO_SHA256}  /tmp/go.tgz" | sha256sum -c - && \
    tar -C /usr/local -xzf /tmp/go.tgz && rm /tmp/go.tgz
ENV PATH=/usr/local/go/bin:$PATH \
    GOPATH=/opt/go \
    GOTOOLCHAIN=local
COPY cdk/go.mod cdk/go.sum /app/collegium/cdk/
RUN cd /app/collegium/cdk && go mod download

# Only cdk/ is needed (the CDK app imports collegium.cdk.* only), so the image is tagged by its content
COPY cdk /app/collegium/cdk
WORKDIR /app/collegium/cdk
RUN go build -o /usr/local/bin/welcome_team ./welcome_team
