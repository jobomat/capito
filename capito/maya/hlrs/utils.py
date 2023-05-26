import hashlib
import json
from pathlib import Path
from shutil import copy
from typing import Tuple, List, Set, Dict

import pymel.core as pc


FOLDERS = {
    "RESOURCES": "resources",
    "LOGS": "logs",
    "IMAGES": "images",
    "SCENES": "ass"
}


def create_shot_folders(location: Path, shot: str):
    location = Path(location)
    shot_dir = location / shot
    shot_dir.mkdir()
    for folder in FOLDERS.values():
        (shot_dir / folder).mkdir()


def collect_resources(image_suffix_list: list=None) -> List[Path]:
    """Collect resource files like images, almbics, standins...
    Returns a list of Paths to each resource.
    Resources found more than once in the scene will only appear once.
    """
    if image_suffix_list is None:
        image_suffix_list = [".png", ".tif", ".tiff", ".exr", ".jpeg", ".jpg", ".bmp"]
    
    files = pc.ls(type="file")
    abcs = pc.ls(type="AlembicNode")
    standins = pc.ls(type="aiStandIn")
    
    filepaths = set()
    
    for file in files:
        filepath = Path(file.fileTextureName.get())
        filepaths.add(filepath)
       
    for abc in abcs:
        filepath = Path(abc.abc_File.get())
        filepaths.add(filepath)
           
    for standin in standins:
        filepath = Path(standin.dso.get())
        filepaths.add(filepath)
    
    return list(filepaths)


def copy_resources(resources: List[Path], dest: Path):
    """Copy the files in resources to the folder dest.
    """
    dest = Path(dest)
    for src in resources:
        try:
            copy(src, dest / src.name)
            print(f"Copying {src}.")
        except FileNotFoundError:
            print(f"File {src} not found.") 
        except PermissionError:
            print(f"No permission for {src}.")


def get_resource_paths(resources: List[Path]) -> List[str]:
    """Returns a list of parent folders of resources
    where each folder only appears once.
    """
    all_paths = [str(p.parent).replace("\\", "/") for p in resources]
    return list(set(all_paths))


def get_pathmap(resources: List[Path]) -> Dict[str, Dict[str, str]]:
    """Returns a pathmap for the given list of resource files
    suitable for creating a Arnold pathmap json file.
    """
    res = {p: FOLDERS["RESOURCES"] for p in get_resource_paths(resources)}
    ocio_conf_file = pc.colorManagementPrefs(q=1, configFilePath=1)
    ocio = str(Path(ocio_conf_file).parent.parent).replace("\\", "/")
    res[ocio] = "OCIO"
    return {
        "windows": res,
        "mac": res,
        "linux": res
    }



def create_hash(file_path: str, buffer_size:int=262144):
    md5 = hashlib.md5()
    #sha1 = hashlib.sha1()
    with open(file_path, 'rb') as file:
        while True:
            data = file.read(buffer_size)
            if not data:
                break
            md5.update(data)
            #sha1.update(data)
    return md5.hexdigest()


def write_pathmap(pathmap: dict, folder: Path):
    """Writes file 'pathmap.json' to folder.
    """
    with open(folder/"pathmap.json", "w") as file:
        json.dump(pathmap, file, indent=4)

    
def export_ass_files():
    pass


def write_jobfiles():
    pass


def write_jobfile():
    pass