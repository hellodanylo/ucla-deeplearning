#!/usr/bin/env zsh

conda env remove -n ucla-dev
conda env create -n ucla-dev -f dev/conda_init.yml
conda env export -n ucla-dev --no-build | sed \$d >dev/conda_lock.yml

conda env remove -n ucla-dev
conda env create -n ucla-dev -f dev/conda_lock.yml

