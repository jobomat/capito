"""
This file contains all the actions to perform by 
eg a cronjob on the hlrs bridge computer.
A cronjob scheduled every minute could be created
by calling crontab -e an inserting the following line:

*/1 * * * * /root/hlrs_venv/bin/python /mnt/cg/pipeline/capito/capito/haleres/cron.py "/mnt/cg/pipeline/capito" "/mnt/cg/pipeline/hlrs/settings.json" >> ~/cron.log 2>&1

It's important to provide the two arguments:
1. The capito path (Path to capito base directory)
2. The path to the haleres settings json.

In the example above the results are logged to a file "cron.log".
The cron.log file will contain every print-output of this python file
aswell as all error-output that occures while executing this python file.
"""
from pathlib import Path
import sys
import subprocess
from datetime import datetime

# First get the parameters:
capito_path = sys.argv[1]
haleres_settings_file = sys.argv[2]

# Make capito availible for import:
sys.path.append(capito_path)
from capito.haleres.settings import Settings
from capito.haleres.job import JobProvider
from capito.haleres.hlrs import HLRS

# Load settings and the job provider
haleres_settings = Settings(haleres_settings_file)
jp = JobProvider(haleres_settings)
hlrs = HLRS(haleres_settings_file)

# Get all relevant data
jobs_to_push = jp.get_jobs_to_push()
unfinished_jobs = jp.get_unfinished_jobs()

# Collect ipc-folders of unfinished jobs and write pull-file (--files-from)
print("------------------------------------------------------------------")
print(datetime.now().strftime("%d.%m.%Y - %H:%M:%S"))
print("------------------------------------------------------------------")
ipc_folder_list = [
    job.get_folder("ipc") for job in unfinished_jobs if job not in jobs_to_push
]
# TODO: pull-file schreiben und rsync rufen.
print(f"Pulling {len(ipc_folder_list)} ipc-folders.")
for folder in ipc_folder_list:
    print(f"    {folder}")

# Submit-limits
current_running_jobs = hlrs.get_current_running_jobs()
submit_list = jp.calculate_submit_limits(
    haleres_settings.hlrs_node_limit - len(current_running_jobs)
)
print(f"Submitting renders for {len(submit_list)} jobs.")
for job in submit_list:
    print(f"    {job.name}: submitting: {job.limit}, remaining: {job.remaining_jobs}")

# Call push script
print(f"Pushing {len(jobs_to_push)} jobs.")
subprocess.run([f"{capito_path}/capito/haleres/ca_shell/push_parallel.sh"])

print("")