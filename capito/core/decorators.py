import sys, os, json
from pathlib import Path
from functools import wraps

from capito.conf.setup import get_project_conf, get_user_conf
from capito.conf.config import Config, CONFIG


def layered_settings(layers=["default", "user"]):
    """Decorator for adding json based settings-management to a class.
    To use this decorator, a default json settings file must exist
    in the same directory as the file where the class is defined.

    layers: Which layers to load. ["default", "project", "projectuser", "user"]
    """
    def wrapper(cls):
        @wraps(cls)
        def _get_layered_settings(self):
            """load the json settings files.
            The default json settings file is always loaded. It is read-only.
            If they exist, the capito project and -user settings are loaded.
            If it exists, a settings file in the users home directory is loaded."""
            _layered_settings = Config()
            json_filename = f"{cls.__name__}.json"
            capito_project_conf = CONFIG.alias.get("capito_project")
            capito_user_conf = CONFIG.alias.get("capito_user")

            cls_project_conf = None
            cls_user_conf = None

            if capito_project_conf:
                cls_project_conf = Path(capito_project_conf).parent / "prefs" / "cls_settings" / json_filename
 
            if capito_user_conf:
                cls_user_conf = Path(capito_user_conf).parent / "prefs" / "cls_settings" / json_filename
 
            settings_files = {
                "default": Path(os.path.abspath(sys.modules[cls.__module__].__file__)).parent / json_filename,
                "project": cls_project_conf,
                "projectuser": cls_user_conf,
                "user": Path.home() / "capito_settings" / json_filename
            }

            for alias in layers:
                filename = settings_files[alias]
                if filename is None:
                    continue
                if not filename.exists():
                    filename.parent.mkdir(parents=True, exist_ok=True)
                    with filename.open("w") as filepointer:
                        json.dump({}, filepointer)
                        
                _layered_settings.load(filename, alias)
            
            return _layered_settings

        setattr(cls, '_get_layered_settings', _get_layered_settings)
        return cls

    return wrapper
