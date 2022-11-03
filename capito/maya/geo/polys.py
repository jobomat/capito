from typing import List

import pymel.core as pc
from capito.maya.viewport import wireframe


def set_vertex_wire_color(
    transform: pc.nodetypes.Transform, color: List[float], alpha: float = 1.0
):
    """Sets vertex and wireframe color of
    all shapes in'transform' to 'color'."""
    pc.polyColorPerVertex(transform, colorRGB=color, a=alpha, cdo=True)
    wireframe.colorize(transform, color)


def read_faceverts(faces: List[pc.MeshFace]) -> List[List[List[float]]]:
    """
    Reads all vertex positions of all faces into a simple data structure.
    [
        [
            [x1,y1,z1], [x2,y2,z2], [x3,y3,z3]
        ],
        [ ... ]
    ]
    """
    obj = faces[0].node()
    face_verts = []
    for face in faces:
        v = []
        for vert_index in face.getVertices():
            pos = obj.vtx[vert_index].getPosition(space="world")
            v.append([pos.x, pos.y, pos.z])
        face_verts.append(v)
    return face_verts


def create_from_faceverts(face_vert_list, merge=0.001):
    """Creates a poly object from data structure buildt with read_faceverts."""
    objects = []
    for face in face_vert_list:
        objects.append(pc.PyNode(pc.polyCreateFacet(ch=False, tx=1, s=1, p=face)[0]))
    if len(objects) > 1:
        combined = pc.polyUnite(objects, ch=0, mergeUVSets=1)
        if merge:
            pc.polyMergeVertex(combined, d=merge, am=0, ch=0)
    else:
        combined = objects[0]
    return combined


def poly_text(text, fontface="", fontsize=12):
    hex_text = " ".join([str(hex(ord(c))[2:]) for c in text])
    type_node = pc.createNode("type")
    type_node.setAttr("textInput", hex_text)
    mesh_node = pc.createNode("mesh")
    # long notation to avoid annoing pymel warning:
    pc.connectAttr(
        "{}.outputMesh".format(type_node.name()), "{}.inMesh".format(mesh_node.name())
    )
    text_transform = mesh_node.getParent()
    pc.delete(text_transform, ch=True)
    text_transform.rename(text)
    pc.sets("initialShadingGroup", e=True, forceElement=text_transform)
    return text_transform
