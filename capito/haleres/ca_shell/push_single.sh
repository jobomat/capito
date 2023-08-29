#!/bin/bash
IPC=$1
STATUS=$2
MOUNT_POINT=$3
HLRS_REMOTE_PATH=$4
HLRS_USER=$5
HLRS_SERVER=$6
WORKSPACE_PATH=$7

touch $STATUS/PUSHING

NOW=$( date '+%F_%H-%M-%S' )
if [ -e $IPC/rsync/pushlog_dryrun.log ]; then
    mv $IPC/rsync/pushlog_dryrun.log "$IPC/rsync/pushlog_dryrun_$NOW.log"
fi 
if [ -e $IPC/rsync/pushlog.log ]; then
    mv $IPC/rsync/pushlog.log "$IPC/rsync/pushlog_$NOW.log"
fi 

rsync -ar --ignore-missing-args \
      --files-from=$IPC/rsync/files_to_push.txt \
      --dry-run \
      --itemize-changes \
      $MOUNT_POINT \
      $HLRS_REMOTE_PATH \
      >> $IPC/rsync/pushlog_dryrun.log

rsync -ar --ignore-missing-args \
      --files-from=$IPC/rsync/files_to_push.txt \
      --log-file=$IPC/rsync/pushlog.log \
      $MOUNT_POINT \
      $HLRS_REMOTE_PATH

if [ $? -eq 0 ]; then
    touch $STATUS/ALL_FILES_PUSHED
    touch $STATUS/READY_TO_RENDER
fi

rm $STATUS/PUSHING

REMOTE_STATUS="${STATUS/"$MOUNT_POINT"/"$WORKSPACE_PATH"}"
rsync -ar $STATUS/ $HLRS_USER@$HLRS_SERVER:$REMOTE_STATUS
