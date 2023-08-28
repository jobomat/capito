from pathlib import Path
import sys


capito_path = sys.argv[1]
haleres_settings_file = sys.argv[2]

sys.path.append(capito_path)
from capito.haleres.settings import Settings
from capito.haleres.job import JobProvider


haleres_settings = Settings(haleres_settings_file)
jp = JobProvider(haleres_settings)

jobs_to_push = jp.get_jobs_to_push()
unfinished_jobs = jp.get_unfinished_jobs()

# collect ipc-folders of unfinished jobs and write pull-file
ipc_folder_list = [
    job.get_folder("ipc") for job in unfinished_jobs if job not in jobs_to_push
]

print(f"There are {len(jobs_to_push)} jobs to push.")
print(f"There are {len(ipc_folder_list)} ipc-folders to pull.")