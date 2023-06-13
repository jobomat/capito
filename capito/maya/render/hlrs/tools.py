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


def parallel_ass_export(ass_file: str, startframe: int, endframe: int, renderlayers: List[pc.nodetypes.RenderLayer]):
    """Exports ass files in background processes.
    ass_file must contain an absolute path plus filename
    but without <RenderLayer> and extension!
    Good: L:/hlrs/scenes/test
    BAD 1: scenes/test <-- relative path 
    BAD 2: L:/hlrs/scenes/test_<RenderLayer>.ass <-- RL + extension
    """
    parapy = get_recommended_parallel_mayapys()
    frames_per_core = math.ceil(
        (endframe - startframe) / parapy
    )
    renderlayer_string = ",".join([l.name() for l in renderlayers])
    print(f"Exporting {(endframe - startframe)} frames")
    print(f"with {len(renderlayers)} render layers ({renderlayer_string})")
    print(f"Exporting {frames_per_core} frames per instance...")
    print(f"Spawning up to {parapy} mayapy instances. Keep an eye on the Taskmanager...")
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
            min(e, endframe),
            renderlayer_string
        ]
        p = mayapy.popen(params)
        processes.append(p)
        
        try:
            p.communicate(timeout=1)
        except TimeoutExpired:
            pass
        print(f"Spawning mayapy instance for frames {s} to {e}.")
        s += frames_per_core
        e += frames_per_core


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
            links.append(Path(filename))
            if filename.endswith(".ass"):
                links.extend(get_links_in_ass(filename))
            in_node = False
    return links


def get_all_standin_links() -> List[str]:
    """Returns paths-strings to all aiStandIn resources in the scene.
    StandIns containing ASS files  will be traversed recursively."""
    files = []
    for standin in pc.ls(type="aiStandIn"):
        file = standin.dso.get()
        files.append(file)
        if file.endswith(".ass"):
            files.extend(get_links_in_ass(file))
    return list(set(files))


def get_standin_links(standin) -> List[str]:
    """Returns paths aiStandIn resources.
    StandIns containing ASS files  will be traversed recursively."""
    files = []
    file = standin.dso.get()
    files.append(Path(file))
    if file.endswith(".ass"):
        files.extend(get_links_in_ass(file))
    return files


def create_link_map() -> dict:
    """Collect nodes with linked files in current maya scene.
    (file, almbic, standin)
    """
    link_map = {}
    for file in pc.ls(type="file"):
        link_map[file] = [Path(file.fileTextureName.get())]
    for abc in pc.ls(type="AlembicNode"):
        link_map[abc] = [Path(abc.abc_File.get())]
    for standin in  pc.ls(type="aiStandIn"):
        link_map[standin] = get_standin_links(standin)
    return link_map



def check_filelist(dir_map:dict) -> Tuple[List[str], List[str]]:
    project_path = pc.workspace.path
    pp_len = len(project_path) + 1
    project_name = pc.workspace.name[3:]
    filelist = []
    messages = []

    for path in create_link_map().values():
        msg = ""
        p = str(path).replace("\\", "/")
        share = dir_map.get(p[:3], "")
        if not share:
            msg += f"Resource has unmapped share ({p[:3]})."
        messages.append(msg)
        filelist.append(f"{share}/{project_name}/{p[pp_len:]}")

    return filelist, messages


def write_syncfile(jobdir: str):
    filelist = []
    for files in create_link_map().values():
        if len(files) == 1:
            filelist.append(files[0])
        elif len(files) > 1:
            filelist.extend(files)
    filelist = list(set([str(f) for f in filelist]))
    (Path(jobdir) / "filelist.txt").write_text("\n".join(filelist))
