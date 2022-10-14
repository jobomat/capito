import json
import os
from pathlib import Path
from typing import Any

from capito.core.asset.flows import FlowProvider


class Config:
    """Class to manage multiple json-based config files.
    Multiple config files can be loaded and given an alias.
    Each file loaded will 'shadow' matching keys of earlier loaded configs.
    That means when a key is requested, the value found in the most recently loaded
    file will be returned (if the key is found - otherwise None will be returned).
    The other configs will not lose their key/value pairs.
    by
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Clear all relevant members"""
        self.configs = {}
        self.config_keys = []
        self.alias = {}
        self.dict = {}
        self.source = {}

    def load(self, config_file: str, alias: str = None):
        """Load a config file. Optionally alias the given config file.
        If no alias is given, the created alias will be "layerX" where
        X is the number of the loaded configs. ("layer0", "layer1"...)
        """
        cfg_path = Path(config_file)
        with cfg_path.open("r", encoding="utf-8") as cfg_filepointer:
            cfg = json.load(cfg_filepointer)
        self.dict = {**self.dict, **cfg}
        self.configs[config_file] = cfg
        self.alias[alias or f"layer{len(self.config_keys)}"] = config_file
        self.config_keys.insert(0, config_file)
        self.source = {**self.source, **{key: config_file for key in cfg}}

    def reload(self):
        """Reload all currently registered config files."""
        self.dict = {}
        for config_file in self.configs:
            self.load(config_file)

    def remove_override(self, key):
        """Removes key/value from the upper most layer (if key  exists)."""
        for i, path in enumerate(self.config_keys[:-1]):
            try:
                del self.configs[path][key]
                next_key = self.config_keys[i + 1]
                self.source[key] = next_key
                self.dict[key] = self.configs[next_key][key]
            except KeyError:
                continue

    def save(self, alias: str):
        """Save a specific config file."""
        file_path = self.alias[alias]
        config = self.configs[file_path]
        with Path(file_path).open("w", encoding="utf-8") as cfp:
            json.dump(config, cfp, indent=4)

    def save_configs(self):
        """Save all config files currently loaded."""
        for file_path, config in self.configs.items():
            with Path(file_path).open("w", encoding="utf-8") as cfp:
                json.dump(config, cfp, indent=4)

    def set(self, alias: str, key: str, value: Any):
        """Set key, value pair to the aliased config file."""
        self.configs[self.alias[alias]][key] = value
        self.dict[key] = value
        self.source[key] = self.configs[self.alias[alias]]

    def get_file_by_alias(self, alias: str):
        """Get the file corresponding to the alias."""
        return self.alias.get(alias, None)

    def __getattr__(self, key):
        val = self.dict.get(key, None)
        if val is not None:
            return val
        return os.environ.get(key, None)

    def __getitem__(self, key):
        val = self.dict.get(key, None)
        if val is not None:
            return val
        return os.environ.get(key, None)


CONFIG = Config()


def reload():
    """Reload Capito Project and User Confs."""
    capito_project_dir_env = os.environ.get("CAPITO_PROJECT_DIR", None)
    if capito_project_dir_env is not None:
        project_dir = Path(capito_project_dir_env)
        if project_dir.exists():
            project_conf_json = project_dir / "capito_conf.json"
            if project_conf_json.exists():
                CONFIG.load(str(project_conf_json), "capito_project")
                CONFIG.flow_provider = FlowProvider()
                capito_username = os.environ.get("CAPITO_USERNAME", None)
                if capito_username is not None:
                    user_conf_json = (
                        project_dir / "users" / capito_username / "user_conf.json"
                    )
                    if user_conf_json.exists():
                        CONFIG.load(str(user_conf_json), "capito_user")


reload()
