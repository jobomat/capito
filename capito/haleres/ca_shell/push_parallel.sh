#!/bin/bash
MOUNT_POINT=$1
HLRS_REMOTE_PATH=$2
SCRIPT_PATH=$(dirname $(realpath -s $0))
HLRS_FOLDERS=/mnt/cg[123]/hlrs/*

for JOBFOLDER in $HLRS_FOLDERS; do
    IPC_DIR=$JOBFOLDER/ipc
    STATUS=$IPC_DIR/status
    if [ ! -e $STATUS/ALL_FILES_PUSHED ] && [ ! -e $STATUS/PUSHING ] && [ -e $STATUS/READY_TO_PUSH ]; then
        $SCRIPT_PATH/push_single.sh $IPC_DIR $STATUS $MOUNT_POINT $HLRS_REMOTE_PATH &
    fi
done
sleep 0.25