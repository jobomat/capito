import hashlib
import json
from pathlib import Path
from shutil import copy
from typing import Tuple, List, Set, Dict
import sys
from subprocess import TimeoutExpired
import math
import os

from plumbum import local
import psutil

import pymel.core as pc


def get_recommended_parallel_mayapys():
    """Will return the estimated number of parallel runable mayapy instances.
    The recommended number is either the number of cores
    or the number of mayapys (+ scene) that will fit into the availible memory.
    """
    free_mem = psutil.virtual_memory()[4]
    ma_size = Path(pc.sceneName()).stat().st_size
    maya_mem = 2_000_000_000
    return min(
        os.cpu_count(),
        math.floor(free_mem / (ma_size + maya_mem))
    )


def parallel_ass_export(ass_file, startframe, endframe):
    parapy = get_recommended_parallel_mayapys()
    frames_per_core = math.ceil(
        (endframe - startframe) / parapy
    )
    print(f"Exporting {(endframe - startframe)} frames...")
    print(f"Starting {parapy} mayapy instances...")
    print(f"Exporting {frames_per_core} frames per instance...")
    s = startframe
    e = startframe + frames_per_core - 1
    
    mayapy = local[str(Path(sys.executable).parent / "mayapy.exe")]
    processes = []

    python_script = str(Path(__file__).parent / 'parallelExporter.py')
    
    while e < endframe + frames_per_core:
        params = [
            python_script,
            str(pc.sceneName()),
            ass_file,
            s,
            min(e, endframe)
        ]
        p = mayapy.popen(params)
        processes.append(p)
        
        try:
            p.communicate(timeout=1)
        except TimeoutExpired:
            pass
        s += frames_per_core
        e += frames_per_core


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


def get_links_in_ass(ass_file: str) -> List[str]:
    """Traverses the given ass file recursively.
    Returns a list of path-strings of all image and procedural
    nodes that where found in all traversed ass files."""
    nodes = ["image\n", "procedural\n"]
    with Path(ass_file).open("r") as file:
        lines = file.readlines()
    links = []
    in_node = False
    for line in lines:
        if line in nodes:
            in_node = True
            continue
        if in_node and line.startswith(" filename"):
            filename = line.replace('"', '')[10:-1]
            links.append(filename)
            if filename.endswith(".ass"):
                links.extend(get_links_in_ass(filename))
            in_node = False
    return links


def get_standin_links() -> List[str]:
    """Returns paths-strings to all aiStandIn resources in the scene.
    StandIns containing ASS files  will be traversed recursively."""
    files = []
    for standin in pc.ls(type="aiStandIn"):
        file = standin.dso.get()
        files.append(file)
        if file.endswith(".ass"):
            files.extend(get_links_in_ass(file))
    return list(set(files))


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
    res = {p: f"<ABSOLUTE_WS_PATH>/{FOLDERS['RESOURCES']}" for p in get_resource_paths(resources)}
    ocio_conf_file = pc.colorManagementPrefs(q=1, configFilePath=1)
    ocio = str(Path(ocio_conf_file).parent.parent).replace("\\", "/")
    res[ocio] = "OCIO"
    return {
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


def export_ass_files(folder, jobname, startframe, endframe, renderlayers, arnold_kwargs=None):
    if arnold_kwargs is None:
        arnold_kwargs = {"expandProcedurals": False, "asciiAss": False}
    current = renderlayers[0].currentLayer()
    for renderlayer in renderlayers:
        renderlayer.setCurrent()
        pc.other.arnoldExportAss(
            f=f"{folder}/{jobname}/ass/{jobname}_<RenderLayer>.ass",
            startFrame=startframe, endFrame=endframe, **arnold_kwargs
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