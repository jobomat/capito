"""
Module holding maya specific variables (Mappings)
and functions for dealing with (maya) environment variables. 
"""
from typing import Any

import pymel.core as pc


FRAME_RATE_MAP = {
    "film": 24,
    "game": 15,
    "pal": 25,
    "ntsc": 30,
    "show": 48,
    "palf": 50,
    "ntscf": 60
}


def setenv(var_name:str, var_content:Any, auto_delimiter:bool=True):
    """set an environment variable.
    If auto_delimiter is True the Variable will be wrapped in double quotes."""
    if auto_delimiter:
        var_content = f'"{var_content}"'
    pc.mel.eval(f'putenv {var_name} {var_content};')


def putenv(var_name:str, var_content:Any):
    """Convenience function. See setenv."""
    setenv(var_name, var_content)


def getenv(var_name:str) -> Any:
    """Get the value of an environment variable."""
    return pc.mel.eval('getenv {};'.format(var_name))

