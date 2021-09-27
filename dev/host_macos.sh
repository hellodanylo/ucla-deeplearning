#!/usr/bin/env bash

brew install wget

cd $HOME
mkdir opt
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh -f -b -p $HOME/opt/miniconda

$HOME/opt/miniconda/bin/conda init bash
$HOME/opt/miniconda/bin/conda init zsh
