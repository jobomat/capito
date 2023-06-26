#!/bin/bash
SCRIPT_PATH=$(dirname $(realpath -s $0))
HLRS_FOLDERS=$SCRIPT_PATH/hlrs/*
#HLRS_FOLDERS=/mnt/cg[123]/hlrs/*

single_push () {
    rsync -ar --ignore-missing-args --files-from=$1 --log-file=$2
}

for JOBFOLDER in $HLRS_FOLDERS; do
    IPC_FOLDER=$JOBFOLDER/ipc
    STATUS=$IPC_FOLDER/STATUS
    if [ ! -e $STATUS/ALL_FILES_PUSHED ] && [ ! -e $STATUS/PUSHING ] && [ -e $STATUS/READY_TO_PUSH ]; then
        single_push $IPC_FOLDER/linked_files.txt $IPC_FOLDER/rsync_push.log &
    else
        echo "Nothing to submit for $JOBFOLDER"
    fi
done
sleep 0.25