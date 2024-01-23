import json
from pathlib import Path
from shutil import copy
import tempfile
from typing import Tuple, List, Set, Dict
from subprocess import TimeoutExpired, check_output
import sys
import math
import os
import uuid

from plumbum import local
import platform

import pymel.core as pc

from capito.haleres.job import Job
from capito.haleres.utils import create_flat_frame_list, create_frame_tuple_list


def get_free_mem():
    """Notloesung wegen Prism psutil import-Konflikt."""
    try:
        import psutil
        return psutil.virtual_memory()[4]
    except:
        if platform.system() == 'Windows':
            systeminfo = check_output(["systeminfo"], encoding="437", universal_newlines=True).split("\n")
            memline = [l for l in systeminfo if l.startswith("Verfügbarer physischer Speicher:")][0]
            mem = int("".join([c for c in memline if c.isnumeric()])) * 1000000
            return mem
    return 0


def get_recommended_parallel_mayapys():
    """Will return the estimated number of parallel runable mayapy instances.
    The recommended number is either the number of cores
    or the number of mayapys (+ scene) that will fit into the availible memory.
    """
    free_mem = get_free_mem()
    ma_size = Path(pc.sceneName()).stat().st_size
    maya_mem = 2_000_000_000
    return min(
        os.cpu_count(),
        math.floor(free_mem / (ma_size + maya_mem))
    )


def parallel_ass_export(file_to_open: Path, job: Job,
                        renderlayers: List[pc.nodetypes.RenderLayer],
                        temp_dir: str):
    """Exports ass files in background processes.
    """
    num_maya_instances = get_recommended_parallel_mayapys()
    
    renderlayer_string = ",".join([l.name() for l in renderlayers])
    
    flat_frame_list = create_flat_frame_list(job.framelist)
    num_frames_total = len(flat_frame_list)
    jobsize = math.ceil(num_frames_total / num_maya_instances)
    frame_tuples = create_frame_tuple_list(job.framelist, jobsize)
    num_exports_total = num_frames_total * len(renderlayers)

    job_id = f"{job.name}_{str(uuid.uuid4())[:8]}"
    temp_status_dir = Path(temp_dir) / job_id / "status"
    print("Creating temp dirs for status/export:")
    temp_export_dir = Path(temp_dir) / job_id / "export"
    temp_status_dir.mkdir(parents=True)
    print(f"Status: {temp_status_dir}")
    temp_export_dir.mkdir(parents=True)
    print(f"Export: {temp_export_dir}")

    mayapy = local[str(Path(sys.executable).parent / "mayapy.exe")]
    processes = []
    python_script = str(Path(__file__).parent / 'parallelExporter.py')

    capito_base = str(Path(__file__).parent.parent.parent.parent.parent)
    
    for start, end in frame_tuples:
        params = [
            python_script,
            str(file_to_open),
            start,
            end,
            renderlayer_string,
            str(temp_export_dir),
            job.name,
            job.share,
            str(temp_status_dir),
            num_exports_total,
            capito_base.replace("\\", "/"),
            job.haleres_settings.settings_file
        ]
        p = mayapy.popen(params)
        processes.append(p)
        
        try:
            p.communicate(timeout=0)
        except TimeoutExpired:
            pass
        print(f"Spawning background Maya instance for frames {start} to {end}.")


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
    if file:
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
        standin_links = get_standin_links(standin)
        if standin_links:
            link_map[standin] = standin_links
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


def write_syncfile(job: Job):
    filelist = []
    for files in create_link_map().values():
        if len(files) == 1:
            filelist.append(files[0])
        elif len(files) > 1:
            filelist.extend(files)
    filelist = list(set([str(f) for f in filelist if str(f) not in (".", "/")]))
    job.linked_files = filelist
