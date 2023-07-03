#!/bin/bash
SCRIPT_PATH=$(dirname $(realpath -s $0))
HLRS_FOLDERS=/mnt/cg[123]/hlrs/*

for JOBFOLDER in $HLRS_FOLDERS; do
    IPC_DIR=$JOBFOLDER/ipc
    STATUS=$IPC_DIR/STATUS
    if [ ! -e $STATUS/ALL_FILES_PUSHED ] && [ ! -e $STATUS/PUSHING ] && [ -e $STATUS/READY_TO_PUSH ]; then
        ./push_single.sh $IPC_DIR $STATUS %(source_dir) %(target_dir) &
    fi
done
sleep 0.25