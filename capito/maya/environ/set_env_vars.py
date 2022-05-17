import platform
from pathlib import Path
import pymel.core as pc
from capito.maya.environ.vars import getenv, putenv


def set_env_vars(env_var_list):
    placeholders = {x["name"]: x["value"] for x in env_var_list}
    placeholders["VERSION_SHORT"] = pc.versions.shortName()
    placeholders["OS"] = platform.system()

    print("\nSTART CAPITO SETUP LOG:")
    for env_var_info in env_var_list:
        replace = env_var_info.get('replace', False)
        recursive = env_var_info.get("recursive", False)
        action = 'Replacing' if replace else 'Adding to'
        value = env_var_info["value"].format(**placeholders)

        print(f"{action} environment variable '{env_var_info['name']}':")
        print(f"\t{value}")

        values = [value]
        if recursive:
            for path in Path(value).rglob("*"):
                if path.is_dir():
                    p = str(path).replace("\\", "/")
                    values.append(p)
                    print(f"\t{p}")

        current_value = getenv(env_var_info['name'])
        if current_value and not replace:
            values.insert(0, current_value)
        putenv(env_var_info['name'], ";".join(values))
    
    print("END CAPITO SETUP LOG.\n")