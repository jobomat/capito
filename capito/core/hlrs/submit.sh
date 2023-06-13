#!/bin/bash
SL=$1
SCRIPT_PATH=$(dirname $(realpath -s $0))
JOB_DIR="${SCRIPT_PATH}/jobs"
STATUS_FILE="${SCRIPT_PATH}/status.txt"
ALL_JOBS_SUBMITTED="${SCRIPT_PATH}/ALL_JOBS_SUBMITTED"
READY_TO_RENDER="${SCRIPT_PATH}/READY_TO_RENDER"

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

# check if statusfile already exists and act accordingly
if [ -e $STATUS_FILE ]; then
    echo "RESUBMITTED: $(date)" >> $STATUS_FILE
    echo "  LIMITING TO MAX $SUBMIT_LIMIT SUBMITS" >> $STATUS_FILE
else
    touch $STATUS_FILE
    echo "INITIAL SUBMIT: $(date)" >> $STATUS_FILE
    echo "  LIMITING TO MAX $SUBMIT_LIMIT SUBMITS" >> $STATUS_FILE
fi

NUMBER_OF_JOBS=$(ls $JOB_DIR/*.sh | wc -l)
SUBMIT_COUNTER=0

LOOP_COUNTER=0
# try to submit all jobfiles
for JOB_FILE in $JOB_DIR/*.sh; do
    # Break if submit limit (script parameter) is reached. (eg. submit.sh 5)
    if [ $LOOP_COUNTER -ge $SUBMIT_LIMIT ]; then
        break
    fi
    # if job file name is NOT detected in status file -> not yet submitted
    if ! grep -q $JOB_FILE $STATUS_FILE; then
        /usr/bin/dos2unix $JOB_FILE
        echo -n "    " >> $STATUS_FILE
        /opt/pbs/bin/qsub -o streams -e streams $JOB_FILE >> $STATUS_FILE
        if [ $? -eq 0 ]; then
            # job submits without error:
            # write status and increment submit & loop counter:
            echo "    $JOB_FILE" >> $STATUS_FILE
            SUBMIT_COUNTER=$((SUBMIT_COUNTER+1))
            LOOP_COUNTER=$((LOOP_COUNTER+1))
        else
            # qsub reports error: maybe job limit reached 
            echo "  qsub ERROR: MAYBE THE HLRS-NODE-LIMIT IS REACHED." >> $STATUS_FILE
            echo "  WAITING FOR NEXT SUBMIT CYCLE." >> $STATUS_FILE
            break
        fi
    else
        # if jobfile WAS detected in statusfile: Increment submit counter
        SUBMIT_COUNTER=$((SUBMIT_COUNTER+1))
    fi
done

if [ $SUBMIT_COUNTER -eq $NUMBER_OF_JOBS ]; then
    echo "DONE: $NUMBER_OF_JOBS JOB FILES SUBMITTED." >> $STATUS_FILE
    touch $ALL_JOBS_SUBMITTED
fi