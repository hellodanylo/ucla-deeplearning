#!/usr/bin/env bash

sagemaker_ffmpeg="/home/ec2-user/SageMaker/setup/miniconda/envs/ucla_deeplearning/bin/ffmpeg"
if [ -f $sagemaker_ffmpeg ]; then
    ffmpeg=$sagemaker_ffmpeg
else
    ffmpeg=$(which ffmpeg)
fi


$ffmpeg -framerate 10 -y -i "$1/%d.png" -r 30 \
	-filter_complex "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
	"$1/output.gif"