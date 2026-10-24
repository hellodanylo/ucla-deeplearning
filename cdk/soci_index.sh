#!/usr/bin/env zsh

# Publishes ${COLLEGIUM_ECR}:${STUDIO_IMAGE_TAG}-soci: the Studio image plus a SOCI index, which lets Studio start the
# app before the whole image is downloaded. The domain uses this tag; the CI notebook job uses the plain one.
# Requires: docker login to ECR, privileged docker, and the plain tag already pushed.

set -eux

project_path=${0:a:h:h}
src="${COLLEGIUM_ECR}:${STUDIO_IMAGE_TAG}"
dst="${COLLEGIUM_ECR}:${STUDIO_IMAGE_TAG}-soci"

# Like the Studio image itself, the index only changes with cdk/docker-studio
if docker manifest inspect "$dst" >/dev/null 2>&1; then
    exit 0
fi

docker build -q -t collegium-soci-helper $project_path/cdk/docker-soci

set +x
registry_password=${REGISTRY_PASSWORD:-$(aws ecr get-login-password --region "$AWS_REGION")}
set -x

# containerd's state goes on a volume: overlayfs snapshots don't work on the container's own overlay root
docker run --rm --privileged \
    -v /var/lib/containerd \
    -e REGISTRY="${COLLEGIUM_ECR%%/*}" -e SRC="$src" -e DST="$dst" -e REGISTRY_PASSWORD="$registry_password" \
    collegium-soci-helper bash -c '
        set -eu
        containerd >/tmp/containerd.log 2>&1 &
        until nerdctl info >/dev/null 2>&1; do sleep 1; done
        echo "$REGISTRY_PASSWORD" | nerdctl login -u AWS --password-stdin "$REGISTRY" >/dev/null
        nerdctl pull -q --unpack=false "$SRC"
        nerdctl image convert --soci "$SRC" "$DST"
        nerdctl push --platform linux/amd64 "$DST"
    '
