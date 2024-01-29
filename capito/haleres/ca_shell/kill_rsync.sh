#!/bin/bash
SHARE=$1
JOBNAME=$2
ADDITIONAL_PATTERN=$3

# get all rsync pids with $ADDITIONAL_PATTERN, $SHARE and $JOBNAME in the command-listing
# $ADDITIONAL_PATTERN could be e.g. "files_to_push" to kill only push actions.
# exclude the listed grep command itself (as it will contain all search-terms)

RSYNC_PIDS=$(ps -eF --no-headers |
    grep "rsync.*$ADDITIONAL_PATTERN.*$SHARE.*$JOBNAME" |
    grep -v grep |
    awk '{ print $2 }')
    
# kill all the found rsyncs for this job:
# kill -9 $PID || continue -> forces immediate shutdown...
for PID in $RSYNC_PIDS; do
    echo "Killing rsync with pid ${PID} ($SHARE, $JOBNAME, $ADDITIONAL_PATTERN)"
    kill $PID || continue
done