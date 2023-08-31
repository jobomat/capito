#!/bin/bash
SCRIPT_PATH=$(dirname $(realpath -s $0))
source $SCRIPT_PATH/settings.sh

if [ ! -e $CRON_LOG_FOLDER ]; then
    mkdir $CRON_LOG_FOLDER
fi

if [ -e $CRON_LOG ]; then
    NOW=$( date '+%F' )
    mv $CRON_LOG "$CRON_LOG_FOLDER/cron_$NOW.log"
fi