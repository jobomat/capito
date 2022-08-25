from pathlib import Path
import site
from capito.conf.config import CONFIG

venvs = [str(Path(CONFIG.CAPITO_BASE_DIR, "venvs", "maya", "Lib", "site-packages"))]
for venv in venvs:
    site.addsitedir(venv)
    print(f"Added '{venv}' as sitedir.")
