#!/bin/bash
touch $2/PUSHING
rsync -avr --ignore-missing-args --files-from=$1/rsync/files_to_push.txt --log-file=$1/rsync/pushlog.log $3 $4
if [ $? -eq 0 ]; then
    touch $2/ALL_FILES_PUSHED
fi
rm $2/PUSHING