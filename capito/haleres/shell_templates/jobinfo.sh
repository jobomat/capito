IPC_FOLDERS=( "submitted" "images_rendering" "images_rendered" )

for JOBFOLDER in %(ws_path)s/cg[123]/hlrs/*; do
    for IPC_FOLDER in "${IPC_FOLDERS[@]}"; do
        FOLDER=$JOBFOLDER/ipc/$IPC_FOLDER
        num=$(find $FOLDER -type f maxdepth 1 | wc -l)
        echo "${FOLDER}:${num}"
    done
done