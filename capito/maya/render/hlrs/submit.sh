#!/bin/bash

jobname=$1
job_dir="${PWD}/$jobname/jobfiles"
echo "$job_dir"
status_file="$job_dir/status.txt"

touch $status_file

all_submitted=0

while [ "$all_submitted" -eq 0 ]; do
    all_submitted=1
    for file in $job_dir/*.Job; do
        jobname=$(basename $file .Job)
        if grep -q $jobname $status_file; then
            echo "Job $jobname already submitted."
        else
            all_submitted=0
            dos2unix $file
            echo "Submitting job $jobname."
            qsub $file
            if [ $? -eq 0 ]; then
                echo "job $file queued"
                echo $jobname >> $status_file
            else
                echo " queue limit reached finish for now."
                break
            fi 
        fi
    done
    sleep 180
done
echo "All jobs in $jobname have been submitted"