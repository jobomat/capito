from typing import List, Tuple
from pathlib import Path

import pymel.core as pc


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


# def collect_external_filepaths() -> List[Path]:
#     """Collect linked files in current maya scene.
#     (images, almbics, standins)
#     Returns a list of Paths to each resource.
#     Resources found more than once in the scene will only appear once.
#     """
#     files = pc.ls(type="file")
#     abcs = pc.ls(type="AlembicNode")
    
#     filepaths = set()
    
#     for file in files:
#         filepath = Path(file.fileTextureName.get())
#         filepaths.add(filepath)
       
#     for abc in abcs:
#         filepath = Path(abc.abc_File.get())
#         filepaths.add(filepath)
           
#     for standin in get_standin_links():
#         filepaths.add(standin)

#     return list(filepaths)


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



def create_rsync_filelist(dir_map:dict) -> Tuple[List[str], List[str]]:
    project_path = pc.workspace.path
    pp_len = len(project_path) + 1
    project_name = pc.workspace.name[3:]
    filelist = []
    messages = []

    for path in collect_external_filepaths():
        msg = ""
        p = str(path).replace("\\", "/")
        share = dir_map.get(p[:3], "")
        if not share:
            msg += f"Resource has unmapped share ({p[:3]})."
        messages.append(msg)
        filelist.append(f"{share}/{project_name}/{p[pp_len:]}")

    return filelist, messages


def write_rsync_file(filelist:List[str], filename:str):
    Path(filename).write_text("\n".join(filelist))

class HLRS:
    def __init__(self):
        self.dir_map = {
            "K:/": "cg",
            "L:/": "cg1",
            "M:/": "cg2",
            "N:/": "cg3"
        }
