#!/usr/bin/env bash

ffmpeg=$(find / -wholename "*ucla_deeplearning/bin/ffmpeg" )


$ffmpeg -framerate 10 -y -i "$1/%d.png" -r 30 \
	-filter_complex "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
	"$1/output.gif"