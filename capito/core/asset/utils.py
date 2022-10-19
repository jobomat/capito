"""Helper functions for asset"""
import re
from difflib import SequenceMatcher
from typing import List, Dict

from capito.conf.config import CONFIG
from capito.core.asset.models import Version

VERSION_REGEX = re.compile(r"\{(.*?)\}")
VERSION_KEYS = VERSION_REGEX.findall(CONFIG.VERSION_FILE)


def get_asset_info_by_filename(filename:str) -> Dict[str, str]:
    """Get asset info extracted out of the filename.
    Returns a dictionary with string keys and values of form:
    {"asset": "ASSET.NAME", "step": "STEP.NAME", "version": "000x",...}
    """
    value_string, extension = filename.split(".")
    values = value_string.split("_")
    values.append(extension)
    map = {k: v for k, v in zip(VERSION_KEYS, values)}
    if map.get("asset") and map.get("step") and map.get("version"):
        return map
    return None

def get_version_by_filename(filename: str) -> Version:
    map = get_asset_info_by_filename(filename)
    if map:
        return CONFIG.asset_provider.get(map["asset"]).steps[map["step"]].versions[int(map["version"])]


def similarity(string1, string2):
    """Get similarity score between 0 and 1 for both words."""
    return SequenceMatcher(None, string1, string2).ratio()


def best_match(word:str, words:List[str]):
    best_match = word
    highscore = 0.0
    for candidate in words:
        sim = similarity(candidate, word)
        if sim > highscore:
            highscore = sim
            best_match = candidate
    return best_match


def sanitize_asset_name(name):
    """Create names that conform to the possibilities of capito assets."""
    allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-"
    name = "".join([c for c in name.replace(" ", "-").replace("_", "-") if c in allowed_chars])
    #  remove leading numbers
    return re.sub(r"^[0-9]*", "", name)
