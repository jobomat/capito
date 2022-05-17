"""Module providing functions to generate and edit Maya ik setups.
"""
from typing import Any, List, Tuple
import pymel.core as pc
from capito.maya.geo.transforms import place_along_curve
from capito.maya.rig.utils import (
    scalefactor_node,
    hierarchy_len,
    locator_at_point,
    insert_normalized_scale_node,
)
from capito.maya.rig.joints import single_joint_ctrl
from capito.maya.util.hirarchies import add_group


def get_solver_type(node: Any) -> str:
    """
    Returns a string representing the Solvertype of the given node
    or None if the given node isn't an IkHandle.
    """
    if not isinstance(node, pc.nodetypes.IkHandle):
        return None
    ik_handle_attr = [
        a for a in pc.selected()[0].listAttr() if "solver" in a.name().lower()
    ][0]
    ik_solver = ik_handle_attr.listConnections()[0]
    return ik_solver.type()


def is_spline_ik_handle(node):
    """Returns if the given node is an ikSplineSolver-Handle."""
    return get_solver_type(node) == "ikSplineSolver"


def ik_stretch(
    ik_handle, pole=None, lock=False, max_stretch=5, name=None, parent_measure_loc=True
):
    """Takes an ik-handle and optional pole vector object.
    Creates node network to stretch the joints if maximal segment length is reached.

    :param ik_handle: The maya ik-handle
    :type ik_handle: :class:`pymel.core.nodetypes.IkHandle`
    :param pole: The pole vector object. Required if lock is True.
    :type pole: :class:`pymel.core.nodetypes.Transform`
    :param lock: If True, enables segment locking to pole and adds "lock" attribute to pole.
    :type lock: bool
    :param max_stretch: Upper limit of the scaling (stretch) factor.
    :type max_stretch: float
    :param name: Prefix for all generated nodes.
    :type name: str

    :returns: A tuple of created nodes (divide node, clamp node, ik-handle group)
    :rtype: Tuple(
        :class:`pymel.core.nodetypes.MultiplyDivide`,
        :class:`pymel.core.nodetypes.Clamp`,
        :class:`pymel.core.nodetypes.Transform`
    )
    :raises: None
    """
    joints = ik_handle.getJointList()
    joints.append(joints[-1].getChildren(type="joint")[0])

    name = name or "{}_{}".format(joints[0].name(), joints[-1].name())

    start_loc = locator_at_point(joints[0], name="{}_start".format(name))
    end_loc = locator_at_point(joints[-1], name="{}_end".format(name))

    div_node = pc.createNode("multiplyDivide", name="{}_stretch_div".format(name))

    div_node, s_e_div_attr = scalefactor_node(
        start_loc,
        end_loc,
        div_node,
        name="{}_start_to_end".format(name),
        initial_len=hierarchy_len(joints[0], joints[-1]),
    )

    clamp_node = pc.createNode("clamp", name="{}_clamp".format(name))
    clamp_node.setAttr("minR", 1)
    clamp_node.setAttr("maxR", max_stretch)

    s_e_div_attr >> clamp_node.inputR

    if pole and lock:
        div_node, s_p_div_attr = scalefactor_node(
            start_loc,
            pole,
            div_node,
            name="{}_start_to_pole".format(name),
            initial_len=hierarchy_len(joints[0], joints[1]),
        )
        div_node, p_e_div_attr = scalefactor_node(
            pole,
            end_loc,
            div_node,
            name="{}_pole_to_end".format(name),
            initial_len=hierarchy_len(joints[1], joints[-1]),
        )

        blend_node = pc.createNode("blendColors", name="{}_lock_blend".format(name))

        s_p_div_attr >> blend_node.color1R
        p_e_div_attr >> blend_node.color1G
        clamp_node.outputR >> blend_node.color2R
        clamp_node.outputR >> blend_node.color2G
        blend_node.outputR >> joints[0].scaleX

        if not pole.hasAttr("pole_lock"):
            pole.addAttr("pole_lock", type="double", k=True, minValue=0, maxValue=1)
        pole.pole_lock >> blend_node.blender

        for joint in joints[1:-1]:
            blend_node.outputG >> joint.scaleX
    else:
        for joint in joints:
            clamp_node.outputR >> joint.scaleX

    ik_grp = add_group(ik_handle)
    pc.parent(end_loc, ik_grp)
    ik_grp.setAttr("visibility", False)

    if parent_measure_loc:
        parent_of_start_joint = joints[0].getParent()
        if parent_of_start_joint is not None:
            pc.parent(start_loc, parent_of_start_joint)

    return (div_node, clamp_node, ik_grp)


class StretchyIK:
    def __init__(self):
        self.script_jobs = []
        self.global_scale_attr = None

    def gui(self):
        win_id = "stretchy_ik_window"
        window_width = 250
        window_height = 255

        if pc.window(win_id, q=1, exists=1):
            pc.deleteUI(win_id)

        with pc.window(
            win_id, title="Stretchy IK Setup", wh=[window_width, window_height]
        ) as self.win:
            with pc.frameLayout(
                borderVisible=False, labelVisible=False, marginWidth=7, marginHeight=7
            ):
                with pc.columnLayout(adj=True, rs=6):
                    self.name_textField = pc.textFieldGrp(
                        label="Name: ",
                        text="",
                        cw2=[40, 2],
                        adj=2,
                        placeholderText="Optional",
                    )

                    pc.separator(h=1)

                    self.add_lock_checkBox = pc.checkBox(
                        label="Add Lock Feature (Pole Required)",
                        value=True,
                        onCommand=self.check_prerequisites,
                        offCommand=self.check_prerequisites,
                    )
                    self.autoparent_checkBox = pc.checkBox(
                        label="Autoparent Measure Locator",
                        value=True,
                        annotation="Make the measure locator a sibling of the start joint.",
                    )

                    with pc.rowLayout(nc=2, cw2=[70, 60], adj=2):
                        pc.text(label="Max Stretch: ")
                        self.max_stretch_floatField = pc.floatField(
                            value=5.0, minValue=1.0, pre=1
                        )

                    pc.separator(h=1)

                    self.global_scale_checkBox = pc.checkBox(
                        label="Add Global Scale Compensation Attribute",
                        value=False,
                        annotation="Supply a global scale attribute for scaleable stretch-setups.",
                        onCommand=self.toggle_scale_enable,
                        offCommand=self.toggle_scale_enable,
                    )

                    self.global_scale_textField = pc.textFieldButtonGrp(
                        label="",
                        editable=False,
                        bl="Set",
                        cw3=(0, 100, 40),
                        adj=2,
                        placeholderText="Select Attribute in Channel Box and:",
                        enable=False,
                        bc=self.set_global_scale_attr,
                    )

                    pc.separator(h=1)

                    self.create_button = pc.button(
                        label="Make IK Stretchy", enable=False, c=self.create_setup
                    )
                    pc.separator(h=1)
                    self.hint_text = pc.text(label="")

        self.script_jobs.append(
            pc.scriptJob(e=("SelectionChanged", self.check_prerequisites))
        )
        self.win.closeCommand(self.kill_script_jobs)
        self.win.setWidthHeight([window_width, window_height])
        self.check_prerequisites()

    def toggle_scale_enable(self, *args):
        self.global_scale_textField.setEnable(
            not self.global_scale_textField.getEnable()
        )
        self.check_prerequisites()

    def set_global_scale_attr(self, *args):
        sel = pc.selected()
        if not sel:
            pc.warning("Please select an object and the attribute in channelbox.")
            self.global_scale_textField.setText("")
            self.global_scale_attr = None
            return

        selected_attrs = pc.mel.eval("selectedChannelBoxAttributes")
        if not selected_attrs:
            pc.warning("Please select the designated scale attribute in channelbox.")
            self.global_scale_textField.setText("")
            self.global_scale_attr = None
            return

        self.global_scale_attr = sel[-1].attr(selected_attrs[0])
        self.global_scale_textField.setText(self.global_scale_attr.name())

    def check_prerequisites(self, *args):
        sel = pc.selected()
        if not sel:
            self.create_button.setEnable(False)
            if self.add_lock_checkBox.getValue():
                self.hint("Select an IK Handle\nand Polevector Object.")
            else:
                self.hint("Select an IK Handle.")
            return
        elif len(sel) == 1:
            if self.add_lock_checkBox.getValue():
                self.hint("Select Pole Object\nor disable 'Add Lock Feature'")
                self.create_button.setEnable(False)
                return
            elif sel[0].type() != "ikHandle":
                self.hint("Selected Object has to be of type 'IkHandle'.")
                self.create_button.setEnable(False)
                return
            else:
                pass
        else:
            if sel[0].type() == "ikHandle":
                pass
            elif sel[1].type() == "ikHandle":
                pass
            else:
                self.hint("One of the selected objects\nhas to be an IK Handle.")
                self.create_button.setEnable(False)
                return

        if self.global_scale_checkBox.getValue():
            if self.global_scale_attr is None:
                self.hint(
                    "Set a global scale attribute\nor disable scale feature checkbox."
                )
                self.create_button.setEnable(False)
                return

        self.create_button.setEnable(True)
        self.hint("")

    def hint(self, text):
        self.hint_text.setLabel(text)

    def create_setup(self, *args):
        sel = pc.selected()
        pole = None
        if len(sel) == 1:
            ik_handle = sel[0]
        else:
            if sel[0].type() == "ikHandle":
                ik_handle = sel[0]
                pole = sel[1]
            else:
                ik_handle = sel[1]
                pole = sel[0]

        name = self.name_textField.getText()

        div_node, clamp_node, ik_grp = ik_stretch(
            ik_handle,
            pole=pole,
            lock=self.add_lock_checkBox.getValue(),
            parent_measure_loc=self.autoparent_checkBox.getValue(),
            max_stretch=self.max_stretch_floatField.getValue(),
            name=name,
        )
        if self.global_scale_checkBox.getValue():
            ns_node = insert_normalized_scale_node(
                div_node.attr("outputX"), self.global_scale_attr, name=name
            )
            if pole:
                ns_node = insert_normalized_scale_node(
                    div_node.attr("outputY"), self.global_scale_attr, ns_node, name
                )
                ns_node = insert_normalized_scale_node(
                    div_node.attr("outputZ"), self.global_scale_attr, ns_node, name
                )

    def kill_script_jobs(self, *args):
        for job in self.script_jobs:
            pc.scriptJob(kill=job, force=True)
