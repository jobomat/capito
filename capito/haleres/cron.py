import inspect
from pathlib import Path
import sys


capito_path = Path(inspect.getfile(lambda: None)).parent.parent.parent
sys.path.append(str(capito_path))

from capito.haleres.settings import Settings
from capito.haleres.job import JobProvider

s = Settings("/mnt/cg/pipeline/hlrs/settings.json")
jp = JobProvider(s)

print(jp.jobs)