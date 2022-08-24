import json
import os
from pathlib import Path


class Config:
    def __init__(self):
        self.reset()
        if self.CAPITO_PROJECT_CONF is not None:
            self.load(self.CAPITO_PROJECT_CONF)
        if self.CAPITO_USER_CONF is not None:
            self.load(self.CAPITO_USER_CONF)

    def reset(self):
        self.configs = {}
        self.config_keys = []
        self.dict = {}
        self.source = {}

    def load(self, config_file: str):
        cfg_path = Path(config_file)
        with cfg_path.open("r") as cfg_filepointer:
            cfg = json.load(cfg_filepointer)
        self.dict = {**self.dict, **cfg}
        self.configs[config_file] = cfg
        self.config_keys.insert(0, config_file)
        self.source = {**self.source, **{key: config_file for key in cfg}}

    def reload(self):
        self.dict = {}
        for config_file in self.configs:
            self.load(config_file)

    def remove_override(self, key):
        for i, path in enumerate(self.config_keys[:-1]):
            try:
                del self.configs[path][key]
                next_key = self.config_keys[i + 1]
                self.source[key] = next_key
                self.dict[key] = self.configs[next_key][key]
            except KeyError as e:
                continue

    def save_configs(self):
        for file_path, config in self.configs.items():
            with Path(file_path).open("w") as fp:
                json.dump(config, fp, indent=4)

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
