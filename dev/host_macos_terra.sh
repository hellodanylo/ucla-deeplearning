#!/usr/bin/env zsh

brew tap hashicorp/tap
brew install hashicorp/tap/terraform

wget -O ~/opt/bin/terragrunt https://github.com/gruntwork-io/terragrunt/releases/download/v0.38.9/terragrunt_darwin_arm64
chmod +x ~/opt/bin/terragrunt

