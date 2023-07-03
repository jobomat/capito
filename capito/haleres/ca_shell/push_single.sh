#!/bin/bash
IPC=$1
STATUS=$2
MOUNT_POINT=$3
HLRS_REMOTE_PATH=$4

touch $STATUS/PUSHING

rsync -avr --ignore-missing-args \
      --files-from=$IPC/rsync/files_to_push.txt \
      --log-file=$IPC/rsync/pushlog.log \
      $MOUNT_POINT \
      $HLRS_REMOTE_PATH

if [ $? -eq 0 ]; then
    touch $STATUS/ALL_FILES_PUSHED
fi

rm $STATUS/PUSHING