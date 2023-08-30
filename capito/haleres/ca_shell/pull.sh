#!/bin/bash
JOB_PATH=$1
source $SCRIPT_PATH/settings.sh

STATUS_DIR=$JOB_PATH/ipc/status
RSYNC_DIR=$JOB_PATH/ipc/rsync

touch $STATUS_DIR/PULLING

NOW=$( date '+%F_%H-%M-%S' )

if [ -e $RSYNC_DIR/pull.log ]; then
    mv $RSYNC_DIR/pull.log "$RSYNC_DIR/pull_$NOW.log"
fi 

rsync -ar --ignore-missing-args \
      --files-from=$RSYNC_DIR/files_to_pull.txt \
      --log-file=$RSYNC_DIR/pull.log \
      $HLRS_REMOTE_PATH \
      $MOUNT_POINT

rm $STATUS_DIR/PULLING
