#!/bin/bash
#PBS -A zmcjbomm
#PBS -N {ASS_FILE}
# PBS -l nodes=1:ppn=24
# PBS -l walltime=00:02:00
#PBS -l select=1:node_type=rome,walltime=0:20:00

export WS_BASE_PATH=$(ws_find {LUSTRE_WORKSPACE_NAME})

# Arnold vars
export ARNOLD_PATH=~/arnold_7.1.3.1
export ADSKFLEX_LICENSE_FILE="@ca-lic.hdm-stuttgart.de"
export ARNOLD_TEXTURE_PATH=$WS_BASE_PATH/{SHOT}/resources

PATH=$PATH:$ARNOLD_PATH/bin/:$ARNOLD_PATH/bin
export PATH

# start rendering
$ARNOLD_PATH/bin/kick \
-nstdin \
-dp -dw -v 5 \
-l $ARNOLD_PATH/shaders \
-set options.texture_searchpath $WS_BASE_PATH/{SHOT}/resources \
-set options.procedural_searchpath $WS_BASE_PATH/{SHOT}/resources \
-set color_manager_ocio.config ~/OCIO/aces_1.2/config.ocio \
-i $WS_BASE_PATH/{SHOT}/ass/{ASS_FILE} \
-o $WS_BASE_PATH/{SHOT}/images/{OUTPUT_FILE}.exr \
&> $WS_BASE_PATH/{SHOT}/logs/{ASS_FILE}.log