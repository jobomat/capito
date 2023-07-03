SCRIPT_PATH=$(dirname $(realpath -s $0))

for HLRS_FOLDER in $SCRIPT_PATH/cg[123]/hlrs/*; do
    echo $HLRS_FOLDER
    echo "$(find $HLRS_FOLDER/ipc/submitted | wc -l)"
done