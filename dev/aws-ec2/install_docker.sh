#!/usr/bin/env bash

sudo apt-get update >/dev/null
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common \
    >/dev/null

echo Installed APT tools

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable" \
   >/dev/null

sudo apt-get update -y >/dev/null
sudo apt-get install -y docker-ce docker-ce-cli >/dev/null

sudo usermod -aG docker ubuntu

systemctl enable docker.service
systemctl restart docker.service

echo Installed Docker

sudo curl -L "https://github.com/docker/compose/releases/download/1.25.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo Installed Docker Compose

sudo wget https://github.com/bcicen/ctop/releases/download/v0.7.3/ctop-0.7.3-linux-amd64 -O /usr/local/bin/ctop >/dev/null
sudo chmod +x /usr/local/bin/ctop

echo Installed ctop
