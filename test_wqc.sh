#!/bin/sh

source /ipl/quarantine/conda/etc/profile.d/conda.sh
conda activate wqc
~/preventAD/wqc/wqc.py \
	--csv ~/preventAD/qc.csv \
	~/preventAD/proc_20210212/*/qc/*.jpg
