#!/usr/bin/env bash

cd $HOME
mkdir opt
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -f -b -p $HOME/opt/miniconda

$HOME/opt/miniconda/bin/conda init