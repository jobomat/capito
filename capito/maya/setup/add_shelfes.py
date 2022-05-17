from pathlib import Path

from capito.maya.ui import shelfes
from capito.maya.environ.vars import getenv


def build_shelfes():
    json_shelf_dir = Path(getenv("CAPITO_RESOURCES")) / "maya" / "shelfes" / "json"

    tls = shelfes.TopLevelShelf()
    for file in json_shelf_dir.glob("*.json"):
        tls.load_from_json(str(file))


build_shelfes()
