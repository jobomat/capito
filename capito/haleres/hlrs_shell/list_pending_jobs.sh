STATUS_DIR="ipc/status"
READY_TO_RENDER="${STATUS_DIR}/READY_TO_RENDER"
ALL_JOBS_SUBMITTED="${STATUS_DIR}/ALL_JOBS_SUBMITTED"
SUBMITTED_DIR="ipc/submitted"

echo "{"
for HLRS_FOLDER in %(ws_path)s/cg[123]/hlrs/*; do
    if [ ! -e "${HLRS_FOLDER}/${READY_TO_RENDER}" ]; then
        continue
    fi
    if [ -e "${HLRS_FOLDER}/${DONE_FILE}" ]; then
        continue
    fi
    NUMBER_OF_JOBS=$(find ${HLRS_FOLDER}/jobs/*.sh -type f | wc -l)
    SUBMITTED_JOBS="$(find ${SUBMITTED_DIR}/*.sh -type f | wc -l)"
    echo "'${HLRS_FOLDER}':$((NUMBER_OF_JOBS-SUBMITTED_JOBS)),"
done
echo "}"