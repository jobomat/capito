export WS_BASE_PATH=$(ws_find {LUSTRE_WORKSPACE_NAME})

# Arnold vars
export ARNOLD_PATH=~/arnold_7.1.3.1
export ADSKFLEX_LICENSE_FILE="@ca-lic.hdm-stuttgart.de"

PATH=$PATH:$ARNOLD_PATH/bin/:$ARNOLD_PATH/bin
export PATH

# start rendering
$ARNOLD_PATH/bin/kick \
-nstdin \
-dp -dw -v 5 \
-l $ARNOLD_PATH/shaders \
-set options.texture_searchpath $WS_BASE_PATH/{PROJECT}/{SHOT}/resources \
-set options.procedural_searchpath $WS_BASE_PATH/{PROJECT}/{SHOT}/resources \
-set color_manager_ocio.config ~/OCIO/aces_1.2/config.ocio \
-i $WS_BASE_PATH/{PROJECT}/{SHOT}/ass/{ASS_FILE} \
-o $WS_BASE_PATH/{PROJECT}/{SHOT}/images/{ASS_FILE}.exr \
&> $WS_BASE_PATH/{PROJECT}/{SHOT}/log/{ASS_FILE}.log