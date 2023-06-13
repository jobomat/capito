#!/bin/bash
#PBS -A zmcjbomm
#PBS -N {jobfile_name}
#PBS -l select=1:node_type=rome
#PBS -l walltime=0:20:00

# For future use:
# PBS -M email-address Sends email notifications to a specific user email address.
# PBS -m [a|b|e] Causes email to be sent to the user when:
# a - the job aborts
# b - the job begins
# e - the job ends

export WS_BASE_PATH=$(ws_find {workspace_name})
export BLENDER_PATH=$WS_BASE_PATH/renderers/{renderer}
export OCIO=$WS_BASE_PATH/Blender-ACES-Config/config.ocio

PATH=$PATH:$BLENDER_PATH/
export PATH

SCENE_FILE=$WS_BASE_PATH/{share_name}/hlrs/{global_job_name}/scenes/{blender_file}

OUTPUT_PATH=$WS_BASE_PATH/{share_name}/hlrs/{global_job_name}/output
LOG_PATH=$WS_BASE_PATH/{share_name}/hlrs/{global_job_name}/logs

# Start rendering
$BLENDER_PATH/blender \
-b $SCENE_FILE \
--log-file $LOG_PATH/{jobfile_name}.log \
-o $OUTPUT_PATH/{global_job_name}.{frame_padding_hashes} \
-E CYCLES \
-s {start_frame} \
-e {end_frame} \
-x 1 \
-a 

{touch_snip}
