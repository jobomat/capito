#!/bin/bash
rsync -ar --ignore-missing-args --files-from=$1 --log-file=$2
