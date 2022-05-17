# coding: utf8
import sys
import os
import json

import pymel.core as pc

from capito.maya.viewport.wireframe import colorize
from capito.maya.geo.shapes import rotate_shapes, set_unrenderable, add_shapes
import capito.maya.geo.curves as curves
from capito.maya.util.names import get_legal_character
import capito.maya.util.hirarchies as hir
from capito.maya.rig.ctrl import slider_control, four_corner_control
from capito.maya.geo.polys import poly_text, set_vertex_wire_color


def import_blendshaped_ik_fk(name="ik_fk"):
    p = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
    pc.mel.eval(
        f'file -import -type "mayaAscii"  -ignoreVersion -mergeNamespacesOnClash false -rpr "ik_fk_icon" -options "v=0;"  -pr  -importFrameRate true  -importTimeRange "override" "{p}/RigIcons/ik_fk_blenshape_icon.ma";'
    )
    ctrl = pc.PyNode("ik_fk_offset_grp|ik_fk_ctrl")
    ctrl.rename(f"{name}_ikfk_ctrl")
    offset = pc.PyNode("ik_fk_offset_grp")
    offset.rename(f"{name}_ikfk_offset_grp")
    return ctrl


this = sys.modules[__name__]
this.icons = None


class RigIcons:
    """
    Maya tool for creating and editing NURBS curve based rig icons.

    import cg.maya.rig.icons as ri

    rig_icons = ri.RigIcons()
    rig_icons.create_rig_icon(1, snap_to=pc.selected()[0])
    """

    def __init__(self, config_file=None):
        # gui elements
        self.window_name = "jbRigIconsWindow"
        self.icon_gridLayout = None
        self.scale_floatSliderGrp = None
        self.color_colorSliderGrp = None
        self.color_buttons = []
        self.icons = []

        # config
        self.module_path = os.path.dirname(os.path.realpath(__file__))
        self.config = {
            "thumbnail_w": 40,
            "thumbnail_h": 40,
            "num_columns": 8,
            "icons_folder": os.path.join(self.module_path, "RigIcons"),
            "palette": [
                [0.0, 0.0, 0.0],
                [1.0, 1.0, 1.0],
                [1.0, 0.9686, 0.0],
                [1.0, 0.7176, 0.0],
                [1.0, 0.0, 0.1647],
                [0.8745, 0.0156, 0.9372],
                [0.6314, 0.1451, 1.0],
                [0.0823, 0.2902, 0.7686],
                [0.0, 0.4823, 1.0],
                [0.0, 1.0, 1.0],
                [0.0, 0.779, 0.4503],
                [0.0, 0.713, 0.0],
                [0.4197, 0.953, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.5, 0.5, 0.5],
            ],
            "std_color": None,
            "ctrl": "_ctrl",
            "offset": "_offset",
            "null": "_null",
        }

        if config_file:
            self.config_file = config_file
        else:
            self.config_file = os.path.join(self.module_path, "RigIcons", "config.json")

        # self.save_config()
        if self.load_config():
            self.load_icons()
        else:
            pc.error("Error loading config.file. Check ScriptEditor for Details.")
        # self.gui()

    def save_config(self):
        with open(self.config_file, mode="w") as f:
            json.dump(self.config, f)

    def load_config(self):
        with open(self.config_file, mode="r") as cf:
            self.config = json.load(cf)
            if not os.path.isdir(self.config["icons_folder"]):
                pc.warning(
                    "The path specified for 'icons_folder' doesn't exist. Check 'RigIcons/config.json'."
                )
            else:
                if not os.path.isfile(
                    os.path.join(self.config["icons_folder"], "icons.json")
                ):
                    pc.warning(
                        "File 'icons.json' missing in '{}'.".format(
                            self.config["icons_folder"]
                        )
                    )
            if os.path.isfile(os.path.join(self.module_path, "RigIcons", "icons.json")):
                self.config["icons_folder"] = os.path.join(self.module_path, "RigIcons")
                print("Using '{}/icons.json'.".format(self.config["icons_folder"]))
                return True
            return False

    def load_icons(self):
        with open(
            os.path.join(self.config["icons_folder"], "icons.json"), mode="r"
        ) as icf:
            if this.icons is None:
                print("Loading icon.json...")
                this.icons = json.load(icf)
            self.icons = this.icons

    def gui(self):
        if pc.window(self.window_name, exists=True):
            pc.deleteUI(self.window_name)

        with pc.window(
            self.window_name,
            title="Rig Icons",
            menuBar=True,
            toolbox=True,
            resizeToFitChildren=True,
            closeCommand=self.save_config,
        ):

            with pc.menu(label="File", tearOff=True):
                pc.menuItem(label="Save Config", c=self.save_config)

            with pc.menu(label="Specials", tearOff=True):
                pc.menuItem(
                    label="IK FK BlendShaped Icon",
                    c=pc.Callback(self.create_ik_fk_blendshaped_icon),
                )
                pc.menuItem(
                    label="Slider from 0 to 1", c=pc.Callback(self.create_slider, False)
                )
                pc.menuItem(
                    label="Slider from -1 to 1", c=pc.Callback(self.create_slider, True)
                )
                pc.menuItem(
                    label="Four Corner Control", c=self.create_four_corner_control
                )
                pc.menuItem(label="Text from Name Field", c=self.create_text)

            with pc.columnLayout(adjustableColumn=True):
                pc.separator(h=10)

                self.name_textFieldGrp = pc.textFieldGrp(
                    label="Name: ",
                    cw2=[40, 242],
                    adj=2,
                    textChangedCommand=self.check_text_field_input,
                    annotation="If left blank, name of selected object OR"
                    "default name will be used.\nTo see the default name, "
                    "hover above the RigIcon-button.\nRightclick for Name-History.",
                    placeholderText="Leave blank for selected object- or defaultname",
                )
                self.nameHistoryPopup = pc.popupMenu()

                pc.separator(h=10)

                with pc.gridLayout(
                    numberOfColumns=self.config["num_columns"],
                    cellWidthHeight=[
                        self.config["thumbnail_w"] + 2,
                        self.config["thumbnail_h"],
                    ],
                ) as self.icon_gridLayout:
                    for i, icon in enumerate(self.icons):
                        self.create_icon_button(i)

                pc.separator(h=10)

                with pc.rowLayout(numberOfColumns=7, adj=7):
                    pc.text(label=" Rotate by ")
                    self.rotation_angle = pc.intField(
                        w=25, h=20, minValue=-180, maxValue=180, value=90
                    )
                    pc.text(label=" in ")
                    pc.button(
                        w=20,
                        h=20,
                        label="x",
                        c=pc.Callback(self.rotate_shape, [1, 0, 0]),
                    )
                    pc.button(
                        w=20,
                        h=20,
                        label="y",
                        c=pc.Callback(self.rotate_shape, [0, 1, 0]),
                    )
                    pc.button(
                        w=20,
                        h=20,
                        label="z",
                        c=pc.Callback(self.rotate_shape, [0, 0, 1]),
                    )
                    with pc.rowLayout(nc=2, cw2=[1, 90], adj=1):
                        pc.text(label=" ")
                        pc.button(
                            label="Enable Centered Scale", c=self.enable_centered_scale
                        )

                pc.separator(h=10)

                with pc.rowLayout(numberOfColumns=len(self.config["palette"])):
                    style = ["iconOnly", "textOnly"]
                    for i, color in enumerate(self.config["palette"]):
                        color_button = pc.iconTextButton(
                            style=style[i == self.config["std_color"]],
                            backgroundColor=color,
                            w=19,
                            h=20,
                            label="# ",
                            font="boldLabelFont",
                            al="left",
                            c=pc.Callback(self.colorize_selected_curves, i),
                        )
                        self.color_buttons.append(color_button)
                        pc.popupMenu()
                        pc.menuItem(
                            label="Use as Standard Color (Toggle)",
                            c=pc.Callback(self.toggle_standard_color, i),
                        )
                        pc.menuItem(
                            label="Choose Color...", c=pc.Callback(self.choose_color, i)
                        )

                pc.separator(h=10)

                with pc.horizontalLayout():
                    pc.iconTextButton(
                        label="Shaded",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.35, 0.4, 0.45),
                        c=pc.Callback(self.set_shapes_attr, "overrideShading", 1),
                    )
                    pc.iconTextButton(
                        label="Unshaded",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.35, 0.4, 0.45),
                        c=pc.Callback(self.set_shapes_attr, "overrideShading", 0),
                    )
                    pc.iconTextButton(
                        label="Selectable",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.4, 0.45, 0.4),
                        c=pc.Callback(self.set_shapes_attr, "overrideDisplayType", 0),
                    )
                    pc.iconTextButton(
                        label="Unselectable",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.4, 0.45, 0.4),
                        c=pc.Callback(self.set_shapes_attr, "overrideDisplayType", 2),
                    )
                    pc.iconTextButton(
                        label="Unrenderable",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.45, 0.4, 0.4),
                        c=pc.Callback(self.set_unrenderable),
                    )

                pc.separator(h=10)

                with pc.horizontalLayout(ratios=[2, 1, 1, 1, 1, 1]):
                    pc.text(label="Toggle Lock+Hide")
                    pc.iconTextButton(
                        label="Trans",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.4, 0.4, 0.4),
                        c=pc.Callback(self.toggle_lock_hide, ["tx", "ty", "tz"]),
                    )
                    pc.iconTextButton(
                        label="Rot",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.4, 0.4, 0.4),
                        c=pc.Callback(self.toggle_lock_hide, ["rx", "ry", "rz"]),
                    )
                    pc.iconTextButton(
                        label="Scale",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.4, 0.4, 0.4),
                        c=pc.Callback(self.toggle_lock_hide, ["sx", "sy", "sz"]),
                    )
                    pc.iconTextButton(
                        label="Vis",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.4, 0.4, 0.4),
                        c=pc.Callback(self.toggle_lock_hide, ["visibility"]),
                    )
                    pc.iconTextButton(
                        label="All",
                        style="textOnly",
                        font="smallPlainLabelFont",
                        bgc=(0.4, 0.4, 0.4),
                        c=pc.Callback(
                            self.toggle_lock_hide,
                            [
                                "tx",
                                "ty",
                                "tz",
                                "rx",
                                "ry",
                                "rz",
                                "sx",
                                "sy",
                                "sz",
                                "visibility",
                            ],
                        ),
                    )

        # self.adjustButtonPanelHeight()

    def create_icon_button(self, i):
        thumbnail = os.path.join(
            self.config["icons_folder"],
            "thumbnails",
            self.icons[i]["thumbnail"] or "temp.bmp",
        )
        button = pc.iconTextButton(
            width=self.config["thumbnail_w"],
            height=self.config["thumbnail_h"],
            style="iconOnly",
            flat=1,
            image1=thumbnail,
            c=pc.Callback(self.create_rig_icons, i),
            ann="{}\nRightcklick for options.".format(self.icons[i]["tooltip"]),
        )
        #     dragCallback=self.dragCallback,
        #     dropCallback=self.dropCallbackSwap
        # )
        # if btn==None:
        pc.popupMenu()
        pc.menuItem(
            label="Replace selected curve shapes",
            c=pc.Callback(self.replace_selected_with_icon, i),
        )
        pc.menuItem(
            label="Set as joint shape", c=pc.Callback(self.add_as_joint_shape, i)
        )
        #     cmds.menuItem(d=True)
        #     cmds.menuItem(label="Take Thumbnail Screenshot", c=partial( self.iconScreenshot, i) )
        #     cmds.setParent('..')
        #    return button
        return button

    def settings_window(self):
        pass

    def create_rig_icons(self, i, group=True, *args):
        name = pc.textFieldGrp(self.name_textFieldGrp, query=True, text=True)
        sel = pc.selected()
        transforms = []

        if len(sel) > 1:
            for j, obj in enumerate(sel):
                n = ""
                if name:
                    n = "{}_{}".format(name, j)
                else:
                    n = obj.name()
                    n = "_".join(n.split("_")[:-1]) or n
                transforms.append(self.create_rig_icon(i, n, group, obj))
        elif len(sel) == 1:
            n = ""
            if name:
                n = name
            else:
                n = sel[0].name()
                n = "_".join(n.split("_")[:-1]) or n
            transforms.append(self.create_rig_icon(i, n, group, sel[0]))
        else:
            transforms.append(self.create_rig_icon(i, name, group))
        pc.select(transforms)

    def create_rig_icon(self, i, name=None, group=True, snap_to=None, *args):
        name = name or self.icons[i]["name"]
        name = name + self.config["ctrl"]
        top_transform = self.create_curve_hirarchy(self.icons[i]["transforms"], name)
        if snap_to and snap_to.hasAttr("tx"):
            cnstr = pc.parentConstraint(snap_to, top_transform)
            pc.delete(cnstr)
        if self.config["std_color"]:
            pc.select(top_transform)
            pc.select(
                [n for n in top_transform.getChildren(ad=True, type="transform")],
                add=True,
            )
            self.colorize_selected_curves(self.config["std_color"])
        if group:
            offset_grp = hir.add_group(
                top_transform, "{}{}".format(name, self.config["offset"])
            )
            hir.add_group(offset_grp, "{}{}".format(name, self.config["null"]))
        return top_transform

    def replace_selected_with_icon(self, index):
        sel = pc.selected()
        for old in sel:
            new = self.create_rig_icon(index, group=False)
            curves.replace_shapes([old, new])
        pc.select(sel)

    def add_as_joint_shape(self, index):
        sel = pc.selected()
        for jnt in [j for j in sel if type(j) == pc.nodetypes.Joint]:
            icon = self.create_rig_icon(index, group=False)
            add_shapes(icon, jnt)
            pc.delete(icon)
        pc.select(sel)

    def create_curve_hirarchy(self, transforms, name):
        t = None
        for transform in transforms:
            crvs = []
            for shape in transform["shapes"]:
                crvs.append(curves.create_curve(shape, name=shape.get("name", name)))
            t = curves.combine_shapes(crvs)
            t.rename(name or transform.get("name"))
            children = transform.get("children", [])
            for child in children:
                c = self.create_curve_hirarchy([child], child["name"])
                pc.parent(c, t)
        return t

    def choose_color(self, i, *args):
        result = pc.colorEditor()
        col = [float(c) for c in result.split()]
        if col[3]:
            pc.iconTextButton(self.color_buttons[i], edit=True, backgroundColor=col[:3])
            self.config["palette"][i] = col[:3]

    def colorize_selected_curves(self, index, *args):
        col = [c**2.2 for c in self.config["palette"][index]]
        for t in pc.selected():
            colorize(t, col)

    def toggle_standard_color(self, index, *args):
        style = ["iconOnly", "textOnly"]
        if self.config["std_color"] == index:
            self.config["std_color"] = None
        else:
            self.config["std_color"] = index
        for i, btn in enumerate(self.color_buttons):
            pc.iconTextButton(
                btn, edit=True, style=style[i == self.config["std_color"]]
            )

    def rotate_shape(self, axes, angle=None):
        angle = angle or pc.intField(self.rotation_angle, q=True, v=True)
        for transform in pc.selected():
            rotate_shapes(transform, [a * angle for a in axes])
            children = transform.getChildren(type="transform")
            pivot = transform.getAttr("worldMatrix")[3][:-1]
            # for child in children:
            #    rotate_shapes(child, [a * angle for a in axes], pivot)

    def enable_centered_scale(self, *args):
        curves = [
            c.getShape()
            for c in pc.selected()
            if type(c.getShape()) == pc.nodetypes.NurbsCurve
        ]
        pc.select(cl=True)
        for crv in curves:
            pc.select(crv.cv, add=True)

        pc.mel.eval("setToolTo $gScale;")
        pc.manipScaleContext("Scale", e=True, useObjectPivot=True, useManipPivot=False)

    def check_text_field_input(self, *args):
        t = self.name_textFieldGrp.getText()
        if not len(t):
            return ""
        pc.textFieldGrp(
            self.name_textFieldGrp,
            edit=True,
            text="{}{}".format(t[:-1], get_legal_character(t[-1])),
        )

    def create_slider(self, two_sided):
        name = self.name_textFieldGrp.getText() or "slider"
        slider_control(name, two_sided)

    def create_four_corner_control(self, *args):
        name = self.name_textFieldGrp.getText() or "fourCorner"
        four_corner_control(name)

    def create_text(self, *args):
        text = self.name_textFieldGrp.getText() or "Text"
        text_transform = poly_text(text)
        if text_transform:
            set_unrenderable(text_transform.getShapes())
            set_vertex_wire_color(
                text_transform, self.config["palette"][self.config["std_color"]]
            )

    def set_shapes_attr(self, attr, value):
        for obj in pc.selected():
            for shape in obj.getShapes():
                shape.setAttr("overrideEnabled", 1)
                shape.setAttr(attr, value)

    def set_unrenderable(self):
        for obj in pc.selected():
            set_unrenderable(obj.getShapes())

    def toggle_lock_hide(self, channels):
        for obj in pc.selected():
            for channel in channels:
                obj.attr(channel).setKeyable(not obj.attr(channel).isKeyable())
                obj.attr(channel).setLocked(not obj.attr(channel).isLocked())

    def create_ik_fk_blendshaped_icon(self):
        import_blendshaped_ik_fk()

    def list(self):
        print(
            "\n".join(
                "{}: {}".format(i, icon["name"]) for i, icon in enumerate(this.icons)
            )
        )


# # Following example shows easy way to save only createNode excerpts
# # from exported NurbsCurve(s) / Polys. Export them as .ma
# # and process them like so:

# from pathlib import Path

# def filter_line(line):
#     if line.lstrip().startswith("rename -uid "):
#         return ""
#     if line.lstrip().startswith('setAttr ".ov'):
#         return ""
#     if line.startswith("\t"):
#         return line


# path = r"C:/Users/jobo/Desktop/"
# name = "test"

# ma_file = Path(path) / f"{name}.ma"
# pc.system.exportSelected(str(ma_file), force=True, type="mayaAscii")

# ma_curves_excerpt =[]
# with ma_file.open("r") as f:
#     lines = f.readlines()

# create_node_detected = False
# for line in lines:
#     if line.startswith("createNode"):
#         create_node_detected = True
#         ma_curves_excerpt.append(line)
#     elif create_node_detected and line.startswith("\t"):
#         ma_curves_excerpt.append(filter_line(line))
#     else:
#         create_node_detected = False

# file = Path(r"C:\Users\jobo\Desktop") / f"{name}.ri"
# with file.open("w") as f:
#     f.write("".join(ma_curves_excerpt))


# # load again:
# with file.open("r") as f:
#     pc.mel.eval(f.read())
