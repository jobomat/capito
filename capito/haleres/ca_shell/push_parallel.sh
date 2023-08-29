#!/bin/bash
SCRIPT_PATH=$(dirname $(realpath -s $0))
source $SCRIPT_PATH/settings.sh

for JOBFOLDER in $HLRS_FOLDERS_REGEX; do
    IPC_DIR=$JOBFOLDER/ipc
    STATUS=$IPC_DIR/status
    if [ ! -e $STATUS/ALL_FILES_PUSHED ] && [ ! -e $STATUS/PUSHING ] && [ -e $STATUS/READY_TO_PUSH ]; then
        $SCRIPT_PATH/push_single.sh $IPC_DIR $STATUS $MOUNT_POINT $HLRS_REMOTE_PATH $HLRS_USER $HLRS_SERVER $WORKSPACE_PATH &
    fi
done
sleep 0.25