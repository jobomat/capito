#!/bin/bash
#PBS -A zmcjbomm
#PBS -N {job_name}
#PBS -l select=1:node_type=rome,walltime=0:20:00

export WS_BASE_PATH=$(ws_find {workspace_name})
export BLENDER_PATH=$WS_BASE_PATH/renderers/{renderer}

PATH=$PATH:$BLENDER_PATH/
export PATH

SCENE_FILE=$WS_BASE_PATH/{share_name}/hlrs/{job_name}/scenes/{blender_file}

OUTPUT_PATH=$WS_BASE_PATH/{share_name}/hlrs/{job_name}/output

# Start rendering
$BLENDER_PATH/blender \
-b $SCENE_FILE \
-o $OUTPUT_PATH/{job_name}.#### \
-F OPEN_EXR \
-E CYCLES \
-s {start_frame} \
-e {end_frame} \
-x 1 \
-a 
