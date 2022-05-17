"""
Module for setting up (maya) environment variables. 
"""
import os
import platform
import json
from typing import Any
from capito.maya.environ.vars import getenv, putenv


def set_env_vars(env_vars:dict, placeholders:dict=None):
    """
    Set Maya Environment Variables via dictionary "env_vars".
    Dictionary Keys:
        "name": The name of the Maya Environment Var.
        "recursive": bool, if True not the folder but all subfolders will be added
        "replace": bool, if True an existing env var value will be replaced
        "values: list, a list of values to add to the env var.
    placeholder:
        A dictionary with "VARNAME": "VARVALUE" pairs.
        The contents of var["values"] may contain python format string syntax
        (e.g. "one/{two}/three"). If the name in curly braces matches with a key
        in the placeholder dict ("VARNAME") it will be replaced by the value
        in the placeholder dict ("VARVALUE").
    Allways availible placeholders are:
        VERSION_SHORT: The short Maya Version (e.g. 2022)
        OS: The operating System (Linux: Linux, Mac: Darwin, Windows: Windows)
    """
    if placeholders is None:
        placeholders = {}
    placeholders["VERSION_SHORT"] = pc.versions.shortName()
    placeholders["OS"] = platform.system()

    for var_info in env_vars:
        var_name = var_info["name"]
        replace = var_info["replace"]
        recursive = var_info["recursive"]
        values = [v.format(**placeholders) for v in var_info["values"]]
        current_value = getenv(var_name).split(";")
        if "" in current_value:
            current_value.remove("")
        current_value = ";".join(current_value)

        if recursive:
            folders = values[:]
            values = []
            for folder in folders:
                for root, *_ in os.walk(folder):
                    values.append(root.replace("\\", "/"))

        if "" in values:
            values.remove("")
        value = ";".join(values)

        if not replace and current_value:
            value = f"{current_value};{value}"

        print(f"\nSetting environment variable '{var_name}':")
        print("\n".join(value.split(";")))
        putenv(var_name, value)