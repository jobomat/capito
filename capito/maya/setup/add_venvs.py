"""Add the maya venvs to site-dir."""
import site
from pathlib import Path

from capito.conf.config import CONFIG

try:
    venvs = [str(Path(CONFIG.CAPITO_BASE_DIR, "venvs", "maya", "Lib", "site-packages"))]
    for venv in venvs:
        site.addsitedir(venv)
        print(f"Added '{venv}' as sitedir.")
except:
    print("Capito venvs not added.")