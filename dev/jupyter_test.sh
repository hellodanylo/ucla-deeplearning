#!/usr/bin/env zsh

dev_dir=${0:a:h}
project_dir=${dev_dir:h}

cd $project_dir

docker exec -it \
    ucla-jupyter \
    python \
    /app/ucla-deeplearning/foundation/jupyter_render.py \
    process 0*_* \
    --execute \
    --render