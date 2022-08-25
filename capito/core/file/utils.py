"""
Helper functions and shortcuts for file handling.
"""
import os
import errno
import shutil
from pathlib import Path


def copytree(src: Path, dst:Path, symlinks=False, ignore=None):
    """Copy a complete dir-structure"""
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def silent_remove(filename:str):
    """Remove a file and do not raise an error if the file doesn't exist.

    :param filename: The absolute path and filename
    :type filename: str
    """
    try:
        os.remove(filename)
    except OSError as err:  # this would be "except OSError, e:" before Python 2.6
        if err.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


def silent_rename(old_name:str, new_name:str):
    """Rename a file and do not raise an error if the file doesn't exist.

    :param old_name: Absolute path and filename
    :type old_name: str
    :param new_name: Abslute path and new filename
    :type new_name: str
    """
    try:
        os.rename(old_name, new_name)
    except OSError as err:  # this would be "except OSError, e:" before Python 2.6
        if err.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred
