JSON_SETTINGS=/mnt/cg/pipeline/hlrs/settings.json
MOUNT_POINT=$(jq -r '.mount_point' $JSON_SETTINGS)
HLRS_USER=$(jq -r '.hlrs_user' $JSON_SETTINGS)
HLRS_SERVER=$(jq -r '.hlrs_server' $JSON_SETTINGS)
WORKSPACE_PATH=$(jq -r '.workspace_path' $JSON_SETTINGS)
HLRS_FOLDERS_REGEX=$(jq -r '.hlrs_folders_regex' $JSON_SETTINGS)

HLRS_REMOTE_PATH="${HLRS_USER}@${HLRS_SERVER}:${WORKSPACE_PATH}"

HLRS_SETTINGS_FOLDER="$(dirname $JSON_SETTINGS)"
CRON_LOG_FOLDER=$HLRS_SETTINGS_FOLDER/cron_logs
CRON_LOG=$CRON_LOG_FOLDER/cron.log
