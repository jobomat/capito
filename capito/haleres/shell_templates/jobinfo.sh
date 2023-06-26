SCRIPT_PATH=$(dirname $(realpath -s $0))

IPC_FOLDERS=( "submitted" "images_rendering" "images_rendered" )

for HLRS_FOLDER in $SCRIPT_PATH/cg[123]/hlrs/*; do
    for IPC_FOLDER in "${IPC_FOLDERS[@]}"; do
        FOLDER=$HLRS_FOLDER/ipc/$IPC_FOLDER
        num=$(ls -f  $FOLDER | wc -l)
        echo "${FOLDER}:${num}"
    done
done