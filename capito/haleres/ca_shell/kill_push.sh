#!/bin/bash
SCRIPT_PATH=$(dirname $(realpath -s $0))
source $SCRIPT_PATH/settings.sh

SHARE=$1
JOBNAME=$2

IPC_DIR="${MOUNT_POINT}/${SHARE}/hlrs/${JOBNAME}/ipc/"
NOW=$( date '+%F_%H-%M-%S' )

$SCRIPT_PATH/kill_rsync.sh $SHARE $JOBNAME "files_to_push" > "${IPC_DIR}/rsync/kill_${NOW}.log" 2>&1
touch "${IPC_DIR}/status/PUSH_ABORTED"