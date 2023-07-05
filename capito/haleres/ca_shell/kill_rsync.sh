#!/bin/bash
SHARE=$1
JOBNAME=$2
ADDITIONAL_PATTERN=$3

# get all rsync pids with $ADDITIONAL_PATTERN, $SHARE and $JOBNAME in the command-listing
# $ADDITIONAL_PATTERN could be e.g. "files_to_push" to kill only push actions...
RSYNC_PIDS=$(ps -eF --no-headers -p $(pidof rsync) |
    grep "rsync.*$ADDITIONAL_PATTERN.*$SHARE.*$JOBNAME" |
    awk '{ print $1 }')
    
# kill all the found rsyncs for this job:
for PID in $RSYNC_PIDS; do
    echo "Killing rsync with pid ${PID} ($SHARE, $JOBNAME, $ADDITIONAL_PATTERN)"
    kill -9 $PID;
done