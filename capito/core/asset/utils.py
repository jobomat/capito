"""Helper functions for asset"""
import re
from difflib import SequenceMatcher
from typing import List


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
