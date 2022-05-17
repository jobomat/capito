"""Functions for storing shader assignments,
exporting shading-networks with assignment-info
and reassigning shaders to geometry according to assignment-info"""
import json
from collections import defaultdict
from pathlib import Path
from typing import List

import pymel.core as pc
from capito.maya.node.tags import get_tag_dict, get_tagged_dag_nodes


def create_shading_manager_node(name: str, asset_tag: str = "") -> pc.nodetypes.Unknown:
    """Create a ShadingManagerNode (smn)"""
    smn = pc.createNode("unknown", n=f"{name}_smn")
    smn.addAttr("sg", multi=True, dt="string")
    smn.addAttr("shaderName", dt="string")
    smn.shaderName.set(name)
    smn.addAttr("assetTag", dt="string")
    smn.assetTag.set(asset_tag)
    smn.addAttr("objectList", dt="string")
    return smn


def create_shader_assignment(
    transforms: List[pc.nodetypes.Transform], name: str, asset_tag: str = ""
):
    """Creates and fills a ShadingManagemntNode for a given list of Transform nodes"""
    shading_groups = []
    shapes = []
    # get a list of all shapes and all shading groups:
    for obj in transforms:
        shapes.append(obj.getShape())
        shading_groups.extend(obj.getShape().connections(type="shadingEngine"))

    # remove existing smn-nodes and add "sg" attribute
    for shading_group in shading_groups:
        if shading_group.hasAttr("sg"):
            nodes = shading_group.attr("sg").listConnections()
            if nodes:
                pc.delete(nodes[0])
        else:
            shading_group.addAttr("sg", at="message")

    smn = create_shading_manager_node(name, asset_tag=asset_tag)
    smn.objectList.set(
        json.dumps([t.name(stripNamespace=True, long=None) for t in transforms])
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
        index = smn.sg.numElements()
        smn.attr(f"sg[{index}]") >> shading_group.sg
        smn.attr(f"sg[{index}]").set(json.dumps(sg_dict))

    return list(set(shading_groups))


def reassign_shaders(
    smn: pc.nodetypes.Unknown, transforms: List[pc.nodetypes.Transform]
):
    """
    Takes a ShaderManagementNode (smn)
    and a list of transforms (which should contain pymel Mesh-Nodes)
    and reassigns shaders according to the smn.
    """
    transform_shape_map = defaultdict(list)
    for t in transforms:
        if not isinstance(t.getShape(), pc.nodetypes.Mesh):
            continue
        shape = [s for s in t.getShapes() if not s.intermediateObject.get()][0]
        transform_shape_map[t.name(stripNamespace=True, long=None)].append(shape)

    # iterate over the sg-multi-channel-attribute (connected to shading groups)
    # load the contained json and assign the faces/shapes to the shading group
    for i in range(smn.sg.numElements()):
        sg_attr = smn.attr(f"sg[{i}]")
        faces_dict = json.loads(sg_attr.get())
        shading_group = sg_attr.listConnections()[0]
        # assign faces, or whole object if list is empty
        for transform, faces in faces_dict.items():
            for shape in transform_shape_map.get(transform, []):
                if shape is None:
                    print(f"Node {transform} not found in list of supplied transforms.")
                    continue
                if faces:
                    pc.sets(shading_group, forceElement=shape.f[faces])
                else:
                    pc.sets(shading_group, forceElement=shape)


def publish_shader(
    transforms: List[pc.nodetypes.Transform], filename: Path, asset_tag: str = ""
):
    """example function for publishing shading networks with smn."""
    shading_groups = create_shader_assignment(transforms, filename.stem, asset_tag)
    pc.select(shading_groups, r=True, ne=True)
    pc.exportSelected(filename)


class ShaderManager:
    """The GUI Class for management of Shader Packets."""

    def __init__(self):
        self.win_id = "shader_manager_win"
        self.smn_dict = {}
        if pc.window(self.win_id, q=1, exists=1):
            pc.showWindow(self.win_id)
            return
        else:
            self.gui()

    def gui(self):
        window_width = 350
        window_height = 400

        if pc.window(self.win_id, q=1, exists=1):
            self.kill_script_jobs()
            pc.deleteUI(self.win_id)

        with pc.window(self.win_id, title="Shader Packet Manager") as self.win:
            with pc.formLayout() as main_fl:
                with pc.columnLayout(adj=True) as top_layout:
                    with pc.horizontalLayout():
                        pc.text(label="EXPORT:", align="left")
                        pc.button(label="All by AssetTag", c=self.export_all)
                        pc.button(label="For Selection")
                    pc.separator(h=15)
                    with pc.horizontalLayout(ratios=(1, 2)):
                        pc.text(label="IMPORT:", align="left")
                        pc.button(
                            label="Import Shader Package", c=self.import_shader_packet
                        )
                    pc.separator(h=15)
                    pc.textField(
                        placeholderText="Type to filter list",
                        tcc=self.fill_smn_list,
                    )
                with pc.horizontalLayout() as list_layout:
                    self.smn_textScrollList = pc.textScrollList(
                        allowMultiSelection=True, selectCommand=self.set_active_smn
                    )
                    with pc.popupMenu():
                        pc.menuItem(
                            "Select All",
                            c=self.select_all_shading_packages,
                        )
                        pc.menuItem(
                            "Refresh List",
                            c=self.create_and_fill,
                        )
                        pc.menuItem(
                            "Delete selected Shader Packages",
                            c=self.delete_shading_package,
                        )
                with pc.columnLayout(adj=True, rs=5) as bottom_layout:
                    pc.button(
                        label="Assign all Shader Packages by Tag",
                        c=self.reassign_all_by_tag,
                    )

                    pc.text(label="ASSIGN SELECTED SHADER PACKAGES:", align="center")
                    with pc.horizontalLayout():
                        pc.button(label="By Tag", c=self.reassign_selected_by_tag)
                        pc.button(
                            label="To Selected Objects",
                            c=self.reassign_selected_to_selection,
                        )
                        pc.button(
                            label="To Hierarchy",
                            c=self.reassign_selected_to_hierarchy,
                        )

        for layout in [top_layout, list_layout, bottom_layout]:
            main_fl.attachForm(layout, "left", 5)
            main_fl.attachForm(layout, "right", 5)

        main_fl.attachForm(top_layout, "top", 5)
        main_fl.attachForm(bottom_layout, "bottom", 5)
        main_fl.attachControl(list_layout, "top", 0, top_layout)
        main_fl.attachControl(list_layout, "bottom", 0, bottom_layout)

        self.create_smn_dict()
        self.fill_smn_list()
        self.script_jobs = [
            # pc.scriptJob(e=("SelectionChanged", self.test)),
            # pc.scriptJob(e=("NameChanged", self.update_ik_menu)),
        ]
        self.win.closeCommand(self.kill_script_jobs)
        self.win.setWidthHeight([window_width, window_height])

    def export_all(self, args):
        transform_dict = get_tag_dict("assetTag", dag=True)
        for asset_tag, object_list in transform_dict.items():
            file_path = pc.fileDialog2(
                fileFilter="*.ma",
                dialogStyle=2,
                fm=0,
                caption=f"{asset_tag} - Shading Packet Export",
            )
            if file_path:
                publish_shader(object_list, Path(file_path[0]), asset_tag)

    def import_shader_packet(self, *args):
        file_path = pc.fileDialog2(fileFilter="*.ma", dialogStyle=2, fm=4)
        if file_path:
            for fp in file_path:
                pc.importFile(fp)
            self.create_smn_dict()
            self.fill_smn_list()

    def fill_smn_list(self, filtertext=None):
        self.smn_textScrollList.removeAll()
        smn_list = (
            self.smn_dict.keys()
            if not filtertext
            else [n for n in self.smn_dict if filtertext in n]
        )
        for name in smn_list:
            self.smn_textScrollList.append(name)

    def make_item_name(self, item):
        return f"{item.name()}  -  ({item.shaderName.get()})"

    def create_smn_dict(self):
        self.smn_dict = {}
        scene_smns = pc.ls(type="unknown", regex="*_smn")
        for smn in scene_smns:
            self.smn_dict[self.make_item_name(smn)] = smn

    def create_and_fill(self, *args):
        self.create_smn_dict()
        self.fill_smn_list()

    def set_active_smn(self, *args):
        print(
            self.smn_dict[self.smn_textScrollList.getSelectItem()[0]].objectList.get()
        )

    def select_children(self, *args):
        children = []
        sel = pc.selected()
        for obj in sel:
            children.extend(obj.getChildren(ad=True, type="transform"))
        pc.select(children, r=True)

    def reassign_all_by_tag(self, *args):
        self.select_all_shading_packages()
        self.reassign_selected_by_tag()

    def reassign_selected_by_tag(self, *args):
        selected_list_item = self.smn_textScrollList.getSelectItem()
        if not selected_list_item:
            pc.warning("Please select a shader packet from list.")
            return
        for smn_key in selected_list_item:
            smn = self.smn_dict[smn_key]
            reassign_shaders(smn, get_tagged_dag_nodes("assetTag", smn.assetTag.get()))
        # for group in groups:
        #     reassign_shaders(smn, group.getChildren(ad=True, type="transform"))

    def reassign_selected_to_selection(self, *args):
        selected_list_item = self.smn_textScrollList.getSelectItem()
        if not selected_list_item:
            pc.warning("Please select a shader packet from list.")
            return
        smn = self.smn_dict[selected_list_item[0]]
        selection = pc.selected(type="transform")
        if not selection:
            pc.warning("Please select objects to assign shaders to.")
            return
        reassign_shaders(smn, selection)

    def reassign_selected_to_hierarchy(self, *args):
        selected_list_item = self.smn_textScrollList.getSelectItem()
        if not selected_list_item:
            pc.warning("Please select a shader packet from list.")
            return
        smn = self.smn_dict[selected_list_item[0]]
        sel = pc.selected()
        for obj in sel:
            children = obj.getChildren(ad=True, type="transform")
            reassign_shaders(smn, children)

    def select_all_shading_packages(self, *args):
        self.smn_textScrollList.selectAll()

    def delete_shading_package(self, *args):
        selected_list_items = self.smn_textScrollList.getSelectItem()
        for item in selected_list_items:
            smn = self.smn_dict[item]
            del self.smn_dict[item]
            pc.delete(smn)
        self.fill_smn_list()
        pc.informBox(
            "Shader Manager Deleted",
            "This only removes shader management nodes!\nThe shading nodes themself still exist.\n\nUse the HyperShade menu 'Edit >> Delete Unused Nodes' to delete them too.",
        )

    def kill_script_jobs(self, *args):
        for job in self.script_jobs:
            pc.scriptJob(kill=job, force=True)


ShaderManager()
