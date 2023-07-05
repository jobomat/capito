#!/bin/bash
SHARE=$1
JOBNAME=$2
ADDITIONAL_PATTERN=$3

# get all rsync pids with $ADDITIONAL_PATTERN, $SHARE and $JOBNAME in the command-listing
# $ADDITIONAL_PATTERN could be e.g. "files_to_push" to kill only push actions...
ALL_RSYNC_PIDS=$(pidof rsync)
if [ -z "$ALL_RSYNC_PIDS" ]; then
    exit 1
fi

RSYNC_PIDS=$(ps -eF --no-headers |
    grep "rsync.*$ADDITIONAL_PATTERN.*$SHARE.*$JOBNAME" |
    grep -v grep |
    awk '{ print $2 }')
    
# kill all the found rsyncs for this job:
for PID in $RSYNC_PIDS; do
    echo "Killing rsync with pid ${PID} ($SHARE, $JOBNAME, $ADDITIONAL_PATTERN)"
    kill -9 $PID || continue
done