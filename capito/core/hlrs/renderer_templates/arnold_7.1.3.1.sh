#!/bin/bash
#PBS -N {jobfile_name}
#PBS -l select=1:node_type=rome,walltime=0:20:00

export WS_BASE_PATH=$(ws_find {workspace_name})
export OCIO=$WS_BASE_PATH/OCIO/aces_1.2/config.ocio

# Arnold vars
export ARNOLD_PATH=$WS_BASE_PATH/renderers/{renderer}
export ADSKFLEX_LICENSE_FILE="@ca-lic.hdm-stuttgart.de"
# export ARNOLD_TEXTURE_PATH=$WS_BASE_PATH...
# export ARNOLD_PLUGIN_PATH =$ARNOLD_PATH/plugins
export ARNOLD_PATHMAP=$WS_BASE_PATH/{share_name}/hlrs/{job_name}/pathmap.json

PATH=$PATH:$ARNOLD_PATH/bin/
export PATH

# start rendering
{kick_snip}