"""
Functions related to shaders and their connections to shapes.
"""
from uuid import uuid4
import json
from typing import Dict, List
from collections import defaultdict
from pathlib import Path

import pymel.core as pc


def get_suid_map() -> Dict[str, pc.nodetypes.ShadingEngine]:
    """Return cached version of the uid map (see above) if force_update is False.
    Else it will regenerate the uid map and return the updated map.
    """
    suid_map = {}
    for shading_group in pc.ls(type="shadingEngine"):
        if shading_group.hasAttr("staticUid"):
            suid_map[shading_group.staticUid.get()] = shading_group
    return suid_map


def add_suid(node):
    """Adds attribute 'staticUid' to given node.
    staticUid contains a non-changing unique identifier string
    useful for identifying nodes between im- and exports.
    (Mayas native uid attribute will change upon exports...)
    """
    if node.hasAttr("staticUid"):
        return
    node.addAttr("staticUid", dt="string")
    node.staticUid.set(str(uuid4()))


def get_shader_assignment(shape: pc.nodetypes.Mesh) -> Dict[str, List[int]]:
    """Reads shader assignment of shape.
    Returns a dict of structure {"<staticUid>": [face indices]}
    The face indices list will be empty if the shader is assigned to the complete shape.
    """
    shading_groups = list(set(shape.connections(type="shadingEngine")))
    assignment_info = {}
    for shading_group in shading_groups:
        members = shading_group.members()
        faces = None
        for mesh_face in members:
            if not mesh_face.startswith(shape.name()):
                continue
            faces = None
            if isinstance(mesh_face, pc.nodetypes.Mesh):
                faces = []
            elif isinstance(mesh_face, pc.general.MeshFace):
                faces = [int(f.split("[")[-1][:-1]) for f in pc.ls(mesh_face, flatten=True)]
            else:
                print("Shape '{}' not of type 'Mesh'. Skipped.")
                return None
            add_suid(shading_group)
            assignment_info[shading_group.staticUid.get()] = faces
    return assignment_info


def write_shader_assignment(shape: pc.nodetypes.Mesh):
    """Write a dictionary returned by function "get_shader_assignment"
    to an attribute named "shaderAssignments" on transform of the given shape.
    """
    sg_assignment_dict = get_shader_assignment(shape)
    if not sg_assignment_dict:
        return
    transform = shape.getParent()
    print(transform)
    if not transform.hasAttr("shaderAssignments"):
        transform.addAttr("shaderAssignments", dt="string")
    transform.shaderAssignments.set(json.dumps(sg_assignment_dict))


def reassign_shaders(shape: pc.nodetypes.Mesh, namespace: str=""):
    """Assign shaders by reading info in attribute "shaderAssignments" written
    by function "write_shader_assignent".
    if "namespace" is not empty it will be added to shading group name.
    """
    transform = shape.getParent()
    if not transform.hasAttr("shaderAssignments"):
        return
    sg_assignment = json.loads(transform.shaderAssignments.get())
    for suid, faces_list in sg_assignment.items():
        shading_group = get_suid_map().get(suid, None)
        if shading_group is None:
            continue
        sg_string = f"{namespace}:{shading_group.name()}"
        if faces_list:
            pc.sets(sg_string, forceElement=shape.f[faces_list])
            continue
        pc.sets(sg_string, forceElement=shape)


def create_assignment_dict(shapes: List[pc.nodetypes.Mesh]) -> Dict[str, Dict[str, List[int]]]:
    """Given a list of Shape nodes return a dict
    wherethe key is the shape nodes parent (transform) name
    and the value is a dict with the staticUids as key and the face indices as value.

    Obtain all shapes in a group:
    for obj in pc.selected():
        shapes = obj.listRelatives(ad=True, type="shape")
        create_assignment_dict(shapes)
    """
    transforms_with_assignment = {}

    for shape in shapes:
        transform = shape.getParent()
        if transform.hasAttr("shaderAssignments"):
            transforms_with_assignment[transform.name()] = json.loads(transform.shaderAssignments.get())
    return transforms_with_assignment


def list_suid_shaders() -> Dict[str, pc.nodetypes.ShadingEngine]:
    """Create a dict where the key is the staticUid of a ShadingGroup
    and the value is a list of all ShadingGroups with this uid.

    Useful for detecting staticUid-Collisions.
    (Each staticUid should only be present once!)
    """
    suid_dict = defaultdict(list)   
    for sg in pc.ls(type="shadingEngine"):
        if sg.hasAttr("staticUid"):
            suid_dict[sg.staticUid.get()].append(sg)
        
    return suid_dict


def list_suid_in_file(file: str):
    shader_file = Path(file)
    with shader_file.open("r") as sf:
        sf_lines = sf.readlines()

    static_uids = []
    for line in sf_lines:
        if line.startswith('\tsetAttr ".staticUid" -type "string" '):
            static_uids.append(line.split('"')[5])

    return static_uids
