# Helper for cdk/soci_index.sh: containerd + nerdctl + SOCI CLI, to add a SOCI index to the Studio image
# (lazy loading in SageMaker Studio: https://docs.aws.amazon.com/sagemaker/latest/dg/soci-indexing.html).
# Amazon Linux 2023 packages all three; the container runs privileged with its own containerd.
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

RUN dnf install -yq containerd nerdctl soci-snapshotter && dnf clean all
