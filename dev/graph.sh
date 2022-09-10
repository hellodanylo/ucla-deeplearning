#!/usr/bin/env zsh

dot -Tsvg dev/tasks.dot >dev/tasks.svg

terragrunt graph-dependencies >dev/terragrunt.dot
dot -Tsvg dev/terragrunt.dot >dev/terragrunt.svg
