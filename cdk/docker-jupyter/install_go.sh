#!/usr/bin/env zsh

set -eux

cd /app
wget -q https://go.dev/dl/go1.25.3.linux-amd64.tar.gz
tar xf go1.25.3.linux-amd64.tar.gz
rm go1.25.3.linux-amd64.tar.gz