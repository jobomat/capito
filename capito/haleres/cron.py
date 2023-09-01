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

# Get local data
jobs_to_push = jp.get_jobs_to_push()
unfinished_jobs = jp.get_unfinished_jobs()
hlrs_server = f"{haleres_settings.hlrs_user}@{haleres_settings.hlrs_server}"

log_list = []
something_happened = False



# PULL IPC FOLDERS
ipc_folder_list = [
    f"{job.share}/hlrs/{job.name}/ipc"
    for job in unfinished_jobs if job not in jobs_to_push
]
if ipc_folder_list:
    something_happened = True
    # Write pullfile
    pullfile_name = str(datetime.now().strftime("pull_ipc_%Y%m%d_%H%M%S.temp"))
    pullfile = Path(pullfile_name)
    pullfile.write_text("\n".join(ipc_folder_list))
    # Call rsync with pullfile - intentionally blocking!
    log_list.append(f"Pulling {len(ipc_folder_list)} ipc-folder(s). Pull-File: {str(pullfile)}")
    subprocess.check_output([
        "rsync", 
        "-ar",
        "--ignore-missing-args",
        f"--files-from={str(pullfile)}",
        f"{hlrs_server}:{haleres_settings.workspace_path}/",
        f"{haleres_settings.mount_point}"
    ])
    pullfile.unlink()

# PULL IMAGES
# Create pull list
if unfinished_jobs:
    something_happened = True
    log_list.append("Pulling images and logs.")
    for job in unfinished_jobs:
        if not job.is_pulling():
            job.write_pull_file()
            # Call rsync for this job
            log_list.append(f"    {job.share}.{job.name}")
            subprocess.Popen([
                f"{capito_path}/capito/haleres/ca_shell/pull.sh", 
                job.jobfolder,
            ])

# SUBMIT
# Submit-limits
current_running_jobs = hlrs.get_current_running_jobs()
submit_list = jp.calculate_submit_limits(
    haleres_settings.hlrs_node_limit - len(current_running_jobs)
)
if submit_list:
    something_happened = True
    log_list.append(f"Submitting jobs ({len(submit_list)})")
    joblist = ",".join([f"{job.share}.{job.name}" for job in submit_list])
    log_list.append(f"    {joblist}")
    hlrs.submit_jobs(submit_list)


# PUSH
if jobs_to_push:
    something_happened = True
    num_jobs = len(jobs_to_push)
    log_list.append(f"Pushing {num_jobs} job{'s' if num_jobs == 1 else ''}.")
    subprocess.run([f"{capito_path}/capito/haleres/ca_shell/push_parallel.sh"])


if something_happened:
    # Write nice header... Nice!
    print("------------------------------------------------------------------")
    print(datetime.now().strftime("%d.%m.%Y - %H:%M:%S"))
    print("------------------------------------------------------------------")
    print("\n".join(log_list))
    print("")
else:
    print(datetime.now().strftime("%d.%m.%Y - %H:%M:%S - No Events"))