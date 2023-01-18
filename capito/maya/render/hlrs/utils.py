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
    "SCENES": "ass",
    "JOBFILES": "jobfiles"
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
    res = {p: f"<ABSOLUTE_PROJECT_PATH>/{FOLDERS['RESOURCES']}" for p in get_resource_paths(resources)}
    ocio_conf_file = pc.colorManagementPrefs(q=1, configFilePath=1)
    ocio = str(Path(ocio_conf_file).parent.parent).replace("\\", "/")
    res[ocio] = "OCIO"
    return {
        "windows": res,
        "mac": res,
        "linux": res
    }


def write_pathmap(pathmap: dict, folder: Path):
    """Writes file 'pathmap.json' to folder.
    """
    with open(folder/"pathmap.json", "w") as file:
        json.dump(pathmap, file, indent=4)


def create_filename(job_name, framenumber, renderlayer):
    rl_name = renderlayer.name()
    rl_name = "masterLayer" if rl_name == "defaultRenderLayer" else rl_name[3:]
    return f"{job_name}_{rl_name}.{framenumber:04d}"


def export_ass_files(folder, jobname, startframe, endframe, renderlayers):
    current = renderlayers[0].currentLayer()
    for renderlayer in renderlayers:
        renderlayer.setCurrent()
        pc.other.arnoldExportAss(
            f=f"{folder}/{jobname}/ass/{jobname}_<RenderLayer>.ass",
            startFrame=startframe, endFrame=endframe, preserveReferences=True
        )
    current.setCurrent()

def write_jobfiles(folder, jobname, lustre_worspace_name):
    """Writes jobfiles based on existing ass files in folder/jobname/ass.
    """
    
    template = (Path(__file__).parent / 'job_template.sh').read_text(encoding='UTF-8')
    
    for assfile in (Path(folder) / jobname / "ass").glob("*.ass"):
        result = template.format(
            SHOT=jobname,
            ASS_FILE=assfile.name,
            OUTPUT_FILE=assfile.stem,
            LUSTRE_WORKSPACE_NAME=lustre_worspace_name
        )
        jobfile = Path(folder) / jobname / FOLDERS["JOBFILES"] / f"{assfile.name}.Job"
        jobfile.write_text(result)