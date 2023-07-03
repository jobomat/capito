#!/bin/bash
SHOT_NAME=$1
# get all rsync pids with "files_to_push" and $SHOT_NAME in the command-listing:
rsync_pids=$(ps -eF --no-headers -p $(pidof rsync) | grep "rsync.*files_to_push.*${SHOT_NAME}" | awk '{ print $1 }')
# kill all the found rsyncs for this job:
for pid in $rsync_pids; do
    kill -9 $pid;
done