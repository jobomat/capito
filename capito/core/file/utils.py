"""
Helper functions and shortcuts for file handling.
"""
import os
import errno
import shutil
import re
from pathlib import Path
import errno


def copytree(src: str, dest: str):
    # Copy the content of
    # source to destination
    try:
        shutil.copytree(src, dest)
    except OSError as err:
        # error caused if the source was not a directory
        if err.errno == errno.ENOTDIR:
            shutil.copy2(src, dest)
        else:
            print("Error: % s" % err)


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


def remove_file_in_tree(filename: str, top_dir: str):
    """Removes all files of name 'filename' in top_dir and its subdirectories."""
    for file in Path(top_dir).rglob(filename):
        silent_remove(str(file))


def copy_template(src: str, dest: str):
    """Copy a template dir/file structure and remove readme.txt placeholders."""
    copytree(src, dest)
    remove_file_in_tree("readme.txt", dest)


def sanitize_name(input_string:str):
    """
    Returns the given input without any unwanted characters.
    """
    allowed ="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"
    output_string = ""
    for char in input_string:
        if char in allowed:
            output_string += char
    return re.sub(r"^[0-9\_]+", "", output_string)