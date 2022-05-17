import inspect
from pathlib import Path
import json

from maya.utils import executeDeferred

from capito.maya.environ.set_env_vars import set_env_vars


executeDeferred("import capito.maya.setup.add_venvs")
executeDeferred("import capito.maya.setup.add_toolbox_buttons")
executeDeferred("import capito.maya.setup.add_shelfes")
#executeDeferred("from capito.maya.plugin.models import Plugins; capito_plugins = Plugins()")


this_file_path = inspect.getfile(lambda: None).replace("\\", "/")

SETUP_DIR = Path(this_file_path).parent
CAPITO_BASE_DIR = SETUP_DIR.parent.parent.parent
RESOURCES_DIR = CAPITO_BASE_DIR / "resources"
ENV_JSON = SETUP_DIR / "maya_envs.json"

with ENV_JSON.open("r") as jf:
    envvars = json.load(jf)

envvars.append({
    "name": "CAPITO_RESOURCES",
    "value": str(RESOURCES_DIR).replace("\\", "/")
})

envvars.append({
    "name": "CAPITO_BASE_DIR",
    "value": str(CAPITO_BASE_DIR).replace("\\", "/")
})

set_env_vars(envvars)
