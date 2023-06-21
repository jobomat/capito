import os
import json
from pathlib import Path


class Settings:
    def __init__(self, settings_file:str):
        settings_dict = json.loads(Path(settings_file).read_text())
        settings_dict["letter_map"] = {
            letter: share
            for share, letter 
            in settings_dict["share_map"].items()
        }

    def __getattr__(self, key):
        val = self.dict.settings_dict(key, None)
        if val is not None:
            return val
        return os.environ.get(key, None)
    
    def share_to_letter(self, share:str):
        return self.settings_dict["share_map"][share]
    
    def letter_to_share(self, letter:str):
        return self.settings_dict["letter_map"][letter]

    @property
    def shares(self):
        return self.settings_dict["share_map"].keys()