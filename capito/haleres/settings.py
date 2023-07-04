import os
import json
from pathlib import Path
from typing import Any


class Settings:
    def __init__(self, settings_file:str):
        self.settings_file = settings_file
        self.settings_dict = json.loads(Path(settings_file).read_text())
        self.settings_dict["letter_map"] = {
            letter: share
            for share, letter 
            in self.settings_dict["share_map"].items()
        }

    def __getattr__(self, key):
        val = self.settings_dict.get(key, None)
        if val is not None:
            return val
        return os.environ.get(key, None)
    
    def share_to_letter(self, share:str):
        return self.settings_dict["share_map"].get(share)
    
    def letter_to_share(self, letter:str):
        return self.settings_dict["letter_map"].get(letter)
    
    def set_value(self, key:str, value:Any):
        self.settings_dict[key] = value

    def save(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.settings_dict, f, indent=4)

    @property
    def shares(self):
        return self.settings_dict["share_map"].keys()