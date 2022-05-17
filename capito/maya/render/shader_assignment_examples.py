"""
Provide examples for usage of shaders module
"""
from pathlib import Path

import pymel.core as pc
from capito.maya.render.shaders import publish_shader, reassign_shaders

###########################################################
# usage example for publishing
# modeler creates a set with suffix geo_set which contains all relevant geo nodes
# all transform (geo) nodes need to have unique names !!!

# this set is used in shading files to publish shader packets for all contained geo:
object_set = pc.ls(type="objectSet", regex="*geo_set")[
    0
]  # *geo_set... * for asset name
transforms = object_set.members()

file_path = pc.fileDialog2(fileFilter="*.ma", dialogStyle=2, fm=0)
if file_path:
    publish_shader(transforms, Path(file_path[0]))


#########################################################################
# for GUI:
shader_packet_list = pc.ls(type="unknown", regex="*_smn")
shader_names = [s.shaderName.get() for s in shader_packet_list]


########################################################
# usage example for reassigning

# import the shading packet and get hold of the ShaderManagerNode
smns = pc.ls(type="unknown", regex="*smn")
smn = smns[0]
# for example one could import an alembic file into a new group
geo_grp = pc.selected()[0]  # say the selected thing is the new group...

transforms = geo_grp.getChildren(ad=True, type="transform")
reassign_shaders(smn, transforms)
