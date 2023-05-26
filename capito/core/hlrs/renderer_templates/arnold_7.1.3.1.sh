#!/bin/bash
#PBS -N {ASS_FILE}
#PBS -l select=1:node_type=rome,walltime=0:20:00

export WS_BASE_PATH=$(ws_find render)
export OCIO=$WS_BASE_PATH/OCIO/aces_1.2/config.ocio

# Arnold vars
export ARNOLD_PATH=$WS_BASE_PATH/arnold_7.1.3.1
export ADSKFLEX_LICENSE_FILE="@ca-lic.hdm-stuttgart.de"
# export ARNOLD_TEXTURE_PATH=$WS_BASE_PATH/{SHOT}/resources
# export ARNOLD_PLUGIN_PATH =$ARNOLD_PATH/plugins
export ARNOLD_PATHMAP=$WS_BASE_PATH/{SHOT}/pathmap.json

PATH=$PATH:$ARNOLD_PATH/bin/
export PATH

# start rendering
$ARNOLD_PATH/bin/kick \
-nstdin -dp -dw -v 5 \
-set color_manager_ocio.config $OCIO \
-i $WS_BASE_PATH/{SHOT}/ass/{ASS_FILE} \
-o $WS_BASE_PATH/{SHOT}/images/{OUTPUT_FILE}.exr \
&> $WS_BASE_PATH/{SHOT}/logs/{ASS_FILE}.log