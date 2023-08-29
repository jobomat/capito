#!/bin/bash
SL=$1
SCRIPT_PATH=$(dirname $(realpath -s $0))
JOBS_DIR="${SCRIPT_PATH}/input/jobs"
IPC_DIR="${SCRIPT_PATH}/ipc"
STATUS_DIR="${IPC_DIR}/status"
SUBMITTED_DIR="${IPC_DIR}/submitted"
PBS_ID_DIR="${IPC_DIR}/pbs_ids"

SUBMIT_LOG_FILE="${IPC_DIR}/submit.log"
ALL_JOBS_SUBMITTED="${STATUS_DIR}/ALL_JOBS_SUBMITTED"
READY_TO_RENDER="${STATUS_DIR}/READY_TO_RENDER"

STREAMS="${IPC_DIR}/streams"
OUT_STREAM="${STREAMS}/out"
ERR_STREAM="${STREAMS}/err"

if [ ! -e $READY_TO_RENDER ]; then
    exit 1
fi

if [ -e $ALL_JOBS_SUBMITTED ]; then
    exit 1
fi

if [ -n "$SL" ]; then
    SUBMIT_LIMIT=$SL
else
    SUBMIT_LIMIT=60
fi

if [ $SUBMIT_LIMIT == 0 ]; then
    exit 1
fi

# check if statusfile already exists and act accordingly
if [ ! -e $SUBMIT_LOG_FILE ]; then
    echo "RESUBMITTED: $(date)" >> $SUBMIT_LOG_FILE
    echo "  LIMITING TO MAX $SUBMIT_LIMIT SUBMITS" >> $SUBMIT_LOG_FILE
else
    touch $SUBMIT_LOG_FILE
    echo "INITIAL SUBMIT: $(date)" >> $SUBMIT_LOG_FILE
    echo "  LIMITING TO MAX $SUBMIT_LIMIT SUBMITS" >> $SUBMIT_LOG_FILE
fi

LOOP_COUNTER=0
# try to submit all jobfiles
for JOB_FILE in $JOBS_DIR/*.sh; do
    # Break if submit limit (script parameter) is reached. (eg. submit.sh 5)
    if [ $LOOP_COUNTER -ge $SUBMIT_LIMIT ]; then
        break
    fi
    # if job file name is NOT detected in submit dir -> not yet submitted
    if [ ! -e $SUBMITTED_DIR/$JOB_FILE ]; then
        /usr/bin/dos2unix $JOB_FILE
        PURE_JOB_FILE_NAME="$(basename $JOB_FILE)"
        PBS_ID=$(/opt/pbs/bin/qsub -o $OUT_STREAM/$PURE_JOB_FILE_NAME -e $ERR_STREAM/$PURE_JOB_FILE_NAME $JOB_FILE)
        PBS_ID=$(echo $PBS_ID | awk -F "." '{print $1}')
        if [ $? -eq 0 ]; then
            # job submits without error:
            # write status and increment submit & loop counter:
            touch $PBS_ID_DIR/$PBS_ID.$PURE_JOB_FILE_NAME
            echo -n "    " >> $SUBMIT_LOG_FILE
            echo $PBS_ID >> $SUBMIT_LOG_FILE
            echo "    $JOB_FILE" >> $SUBMIT_LOG_FILE
            touch $SUBMITTED_DIR/$PURE_JOB_FILE_NAME
            LOOP_COUNTER=$((LOOP_COUNTER+1))
        else
            # qsub reports error: maybe job limit reached 
            echo "  qsub ERROR: MAYBE THE HLRS-NODE-LIMIT IS REACHED." >> $SUBMIT_LOG_FILE
            echo "  WAITING FOR NEXT SUBMIT CYCLE." >> $SUBMIT_LOG_FILE
            break
        fi
    fi
done

NUM_JOBS_SUBMITTED=$(find $SUBMITTED_DIR/* | wc -l)
NUMBER_OF_JOBS=$(find $JOBS_DIR/* | wc -l)

if [ $NUM_JOBS_SUBMITTED == $NUMBER_OF_JOBS ]; then
    echo "DONE: $NUMBER_OF_JOBS JOB FILES SUBMITTED." >> $SUBMIT_LOG_FILE
    touch $ALL_JOBS_SUBMITTED
fi