"""
Module providing Classes and Functions for dealing with
Look definition, assignment and management.

A Look is defined by on or more shaders an information about
their assignment to a polygonal model or faces of a polygonal model.
"""
import json
from collections import defaultdict
from typing import Any, List

import pymel.core as pc


def create_look_node(name: str, asset: str = None) -> pc.nodetypes.Network:
    """Creates a node of type 'Network' and adds the look node attributes."""
    look_node = pc.createNode("network", name=f"{name}_look")
    look_node.addAttr("sg", multi=True, dt="string")
    look_node.addAttr("lookName", dt="string")
    look_node.lookName.set(name)
    look_node.addAttr("asset", dt="string")
    look_node.asset.set(asset or "")
    look_node.addAttr("objectList", dt="string")
    return look_node


def list_look_nodes() -> List[pc.nodetypes.Network]:
    """List all selected Look nodes in scene"""
    return[node for node in pc.ls(type="network") if node.hasAttr("lookName")]


class Look:
    """Class representing the Look of specific objects in Maya"""

    def __init__(self, name_or_node: Any, asset_name: str = None):
        if isinstance(name_or_node, str):
            self.look_node = create_look_node(name_or_node, asset_name)
        elif isinstance(name_or_node, pc.nodetypes.Network):
            self.look_node = name_or_node

    @property
    def name(self):
        """Returns the Look name (which is different from the node name!)."""
        return self.look_node.lookName.get()

    @property
    def asset(self):
        """Returns the asset which this look belongs to."""
        return self.look_node.asset.get()

    def rename(self, name: str):
        """Renames and keeps node name and lookName field in sync."""
        self.look_node.lookName.set(name)
        self.look_node.rename(f"{name}_look")

    def reset(self):
        """ Resets sg channels by deleting and recreating sg attribute."""
        self.look_node.deleteAttr("sg")
        self.look_node.addAttr("sg", multi=True, dt="string")

    def read(self, transforms: List[pc.nodetypes.Transform]):
        """Detect the shading assignment for a given list of Transform nodes
        and create and fill the channels of self.look_node.
        """
        shading_groups = []
        shapes = []
        # get a list of all shapes and all shading groups:
        for obj in transforms:
            shapes.append(obj.getShape())
            shading_groups.extend(
                obj.getShape().connections(type="shadingEngine"))

        for shading_group in shading_groups:
            if not shading_group.hasAttr("sg"):
                shading_group.addAttr("sg", at="message")

        self.reset()

        self.look_node.objectList.set(
            json.dumps([t.name(stripNamespace=True, long=None)
                        for t in transforms])
        )

        # get assignment info for each shading_group.
        # [objectname: [face1, face2...]
        # empty list = whole object / all faces are assigned
        for shading_group in set(shading_groups):
            if shading_group.name() == "initialShadingGroup":
                continue
            members = shading_group.members()
            sg_dict = {}
            for member in members:
                if member.node() in shapes:
                    if isinstance(member, pc.nodetypes.Mesh):
                        sg_dict[
                            member.getParent().name(stripNamespace=True, long=None)
                        ] = []
                    elif isinstance(member, pc.general.MeshFace):
                        facelist = [
                            int(f.split("[")[-1][:-1]) for f in pc.ls(member, flatten=True)
                        ]
                        sg_dict[
                            member.node().getParent().name(stripNamespace=True, long=None)
                        ] = facelist
            index = self.look_node.sg.numElements()
            self.look_node.attr(f"sg[{index}]") >> shading_group.sg
            self.look_node.attr(f"sg[{index}]").set(json.dumps(sg_dict))

    def assign(self, transforms: List[pc.nodetypes.Transform]):
        """
        Assigns shaders according to the look_node to the given transfroms.
        """
        transform_shape_map = defaultdict(list)
        for transform in transforms:
            if not isinstance(transform.getShape(), pc.nodetypes.Mesh):
                continue
            shape = [s for s in transform.getShapes(
            ) if not s.intermediateObject.get()][0]
            transform_shape_map[transform.name(
                stripNamespace=True, long=None)].append(shape)

        # iterate over the sg-multi-channel-attribute (connected to shading groups)
        # load the contained json and assign the faces/shapes to the shading group
        for i in range(self.look_node.sg.numElements()):
            sg_attr = self.look_node.attr(f"sg[{i}]")
            faces_dict = json.loads(sg_attr.get())
            shading_group = sg_attr.listConnections()[0]
            # assign faces, or whole object if list is empty
            for transform, faces in faces_dict.items():
                for shape in transform_shape_map.get(transform, []):
                    if shape is None:
                        print(
                            f"Node {transform} not found in list of supplied transforms.")
                        continue
                    if faces:
                        pc.sets(shading_group, forceElement=shape.f[faces])
                    else:
                        pc.sets(shading_group, forceElement=shape)
