from pathlib import Path
import sys


capito_path = sys.argv[1]
haleres_settings_file = sys.argv[2]

print(capito_path, haleres_settings_file)

# sys.path.append(str(capito_path))

# from capito.haleres.settings import Settings
# from capito.haleres.job import JobProvider

# haleres_settings = Settings(haleres_settings_file)
# jp = JobProvider(haleres_settings)

# print(jp.jobs)