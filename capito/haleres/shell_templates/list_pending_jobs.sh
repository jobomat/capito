READY_FILE="READY_TO_RENDER"
DONE_FILE="ALL_JOBS_SUBMITTED"

for HLRS_FOLDER in <WS_PATH>/cg[123]/hlrs/*; do
    if [ ! -e "${HLRS_FOLDER}/${READY_FILE}" ]; then
        continue
    fi
    if [ -e "${HLRS_FOLDER}/${DONE_FILE}" ]; then
        continue
    fi
    NUM_JOBS=$(ls ${HLRS_FOLDER}/jobs | wc -l)
    SUBMITTED="$(grep -o $HLRS_FOLDER ${HLRS_FOLDER}/status.txt | wc -l)"
    echo "${HLRS_FOLDER}:$((NUM_JOBS-SUBMITTED))"
done
