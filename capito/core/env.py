import platform
import subprocess
import os


def set_os_env_var(key: str, value: str):
    """Set an environment variable on the OS."""
    set_cmd_by_os = {
        "Windows": f'setx {key} "{value}"',
        "Linux": f'export {key}="{value}"',
        "Darwin": f'export {key}="{value}"'
    }
    subprocess.Popen(set_cmd_by_os[platform.system()], shell=True)
    # Additionally set so, that it will be immediately accessible inside the calling app.
    os.environ[key] = value
    