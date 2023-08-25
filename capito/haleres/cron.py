from pathlib import Path
import sys


capito_path = sys.argv[1]
haleres_settings_file = sys.argv[2]

sys.path.append(capito_path)
from capito.haleres.settings import Settings
from capito.haleres.job import JobProvider


haleres_settings = Settings(haleres_settings_file)
jp = JobProvider(haleres_settings)

for job in jp.jobs:
    print(f"{job.name}: Should be pushed: {job.is_ready_to_push() and not job.is_pushing()}")