from typing import Tuple

import pymel.core as pc

from capito.maya.geo.curves import get_curve_length
from capito.maya.rig.utils import insert_normalized_scale_node
from capito.maya.rig.joints import create_joint_controls_along_curve, get_twist_axis, guess_forward_axis
from capito.maya.ui.maya_gui import get_selected_channelbox_attributes


def get_joint_list(ik_handle: pc.nodetypes.IkHandle):
    start_joint = ik_handle.getStartJoint()
    current_joint = ik_handle.getEndEffector().getParent()
    joint_list = []
    while True:
        joint_list.append(current_joint)
        if current_joint == start_joint:
            break
        current_joint = current_joint.getParent()
    return list(reversed(joint_list))


def create_spline_ik(
    start_joint: pc.nodetypes.Joint,
    end_joint: pc.nodetypes.Joint,
    name: str = None,
    curve_spans: int = 4,
) -> Tuple[pc.nodetypes.IkHandle, pc.nodetypes.NurbsCurve, str]:
    """Mini wrapper around splineIk creation. Enables more than 4 spans."""
    name = name or "".join(start_joint.name[:-1])
    ik_handle, ik_effector, ik_curve = pc.ikHandle(
        n="{}_spline_ik".format(name), sol="ikSplineSolver", pcv=False, ns=curve_spans
    )
    ik_curve.rename("{}_ik_crv".format(name))
    ik_effector.rename("{}_spline_effector".format(name))
    ik_handle.visibility.set(False)
    ik_handle.addAttr("scale_power", k=True)
    ik_curve.visibility.set(False)
    return ik_handle, ik_curve, name


def recommend_up_vector(ik_handle, spline_ik_joint, up_object):
    """
    Returns the recommended up vector value for the advanced twist control up vector.
    The spline_ik_joint is the joint driven by the spline ik solver.
    The up_object is the object controlling the twist.
    """
    # ik handle attribute dWorldUpAxis-codes are as follows:
    # 0: +y | 1: -y | 2: ?y | 3: +z | 4: -z | 5: ?z | 6: +x | 7: -x | 8: ?x
    axes_map = (
        (0, 1, 0),
        (0, -1, 0),
        (0, 1, 0),
        (0, 0, 1),
        (0, 0, -1),
        (0, 0, 1),
        (1, 0, 0),
        (-1, 0, 0),
        (1, 0, 0),
    )
    translate_values = axes_map[ik_handle.dWorldUpAxis.get()]

    ref_loc = pc.spaceLocator(p=(0, 0, 0))
    pc.delete(pc.pointConstraint(up_object, ref_loc, mo=False))
    pc.delete(pc.orientConstraint(spline_ik_joint, ref_loc, mo=False))

    loc = pc.spaceLocator(p=(0, 0, 0))
    pc.parent(loc, ref_loc)
    loc.setTranslation(translate_values)
    pc.parent(loc, up_object, absolute=True)
    new_translate_values = loc.translate.get()

    pc.delete(loc, ref_loc)
    return new_translate_values


def create_curve_based_scale_setup(
    ik_handle: pc.nodetypes.IkHandle, name: str = None
) -> Tuple[pc.nodetypes.CurveInfo, pc.Attribute]:
    """
    Sets up the forward-axis-scaling of joints that are members of 'ik_handle'
    based on the ration of current curve length to original curve length.
    """
    joints = get_joint_list(ik_handle)
    if name is None:
        name = joints[0].name()
    ik_curve = pc.PyNode(ik_handle.getCurve())

    crv_info = pc.createNode("curveInfo", name=f"{name}_ik_crvinfo")
    div_node = pc.createNode("multiplyDivide", name=f"{name}_ik_div")
    div_node.setAttr("operation", 2)
    ik_curve.worldSpace >> crv_info.inputCurve
    crv_info.arcLength >> div_node.input1X
    div_node.setAttr("input2X", crv_info.getAttr("arcLength"))

    axis_map = {
        (1,0,0): "scaleX", (0,1,0): "scaleY", (0,0,1): "scaleZ" 
    }
    for joint in joints:
        div_node.outputX >> joint.attr(axis_map[guess_forward_axis(joint)])

    return crv_info, div_node.attr("outputX")


def setup_advanced_twist_control(
    ik_handle: pc.nodetypes.IkHandle,
    start_up_obj: pc.nodetypes.Transform,
    end_up_obj: pc.nodetypes.Transform,
):
    """
    Sets the advanced twist controls of a spline ik to "Object Rotation Up (Start/End)".
    X has to be the twist axis.
    Y will be set to be the up axis.
    The up axis will be bound to the Y axis of start_up_obj and end_up_obj.
    """
    ik_handle.dWorldUpType.set(4)  # Type: Object rotation up (start/end)
    start_joint = ik_handle.getStartJoint()
    end_joint = ik_handle.getEndEffector().getParent()
    twist_axis = get_twist_axis(start_joint)
    forward_axis_map = {
        (1, 0, 0): 0,
        (-1, 0, 0): 1,
        (0, 1, 0): 2,
        (0, -1, 0): 3,
        (0, 0, 1): 4,
        (0, 0, -1): 5,
    }
    fa = forward_axis_map[twist_axis]
    ik_handle.dForwardAxis.set(fa)
    up_axis_map = [0, 0, 3, 3, 6, 6]
    ik_handle.dWorldUpAxis.set(up_axis_map[fa])
    ik_handle.dWorldUpVector.set(
        recommend_up_vector(ik_handle, start_joint, start_up_obj)
    )
    ik_handle.dWorldUpVectorEnd.set(
        recommend_up_vector(ik_handle, end_joint, end_up_obj)
    )

    start_up_obj.attr("worldMatrix[0]") >> ik_handle.dWorldUpMatrix
    end_up_obj.attr("worldMatrix[0]") >> ik_handle.dWorldUpMatrixEnd

    ik_handle.dTwistControlEnable.set(True)


def setup_squash_stretch(
    ik_handle: pc.nodetypes.IkHandle, scale_factor_attr: pc.Attribute, name: str
):
    """
    Creates an expression and frameCache based setup for preserving the volume
    when a stretchy splineIK is squashed/stretched.
    """
    joint_list = get_joint_list(ik_handle)
    if not ik_handle.hasAttr("scale_power"):
        ik_handle.addAttr("scale_power", at="float")
    scale_power_attr = ik_handle.attr("scale_power")
    scale_power_attr.setKey(t=1, v=0)
    scale_power_attr.setKey(t=len(joint_list), v=0)
    anim_curve_node = scale_power_attr.listConnections()[0]
    anim_curve_node.setWeighted(True)
    pc.keyTangent(anim_curve_node, e=True, absolute=True, t=1, outAngle=50)
    pc.keyTangent(
        anim_curve_node, e=True, absolute=True, t=len(joint_list), inAngle=-50
    )

    axes_map = {
        (1,0,0): ["sx", "sy", "sz"],
        (0,1,0): ["sy", "sx", "sz"],
        (0,0,1): ["sz", "sy", "sz"]
    }
    frame_caches = []
    expression = [f"$scale = {scale_factor_attr.name()};", f"$sqrt = 1 / sqrt($scale);"]
    for i, joint in enumerate(joint_list, 1):
        frame_cache = pc.createNode("frameCache", n=f"{name}_{joint.name()}_fcache")
        frame_cache.varyTime.set(i)
        scale_power_attr >> frame_cache.stream
        forward_axis = guess_forward_axis(joint)
        expression.append(
            f"{joint.name()}.{axes_map[forward_axis][1]} = pow($sqrt, {frame_cache.name()}.varying);"
        )
        expression.append(
            f"{joint.name()}.{axes_map[forward_axis][2]} = pow($sqrt, {frame_cache.name()}.varying);"
        )
        frame_caches.append(frame_cache)

    expression = "\n".join(expression)
    expression_node = pc.expression(s=expression, n=f"{name}_expr")
    return expression_node, frame_caches


class SplineIKRig:
    """Provides and manages functionality for spline ik setups."""

    def __init__(self, ik_handle: pc.nodetypes.IkHandle):
        self.ik_handle = ik_handle
        self._tag = (
            "spline_ik_handle"  # do not change or backwards compatibiliy will break
        )
        self.initial_dropoff_rate: float = 4.0
        # add necessary attributes to ik_handle
        for attr in [
            "control_joints",
            "controls",
            "stretch_div",
            "skin_cluster",
            "curve_info",
        ]:
            if not self.ik_handle.hasAttr(attr):
                self.ik_handle.addAttr(attr, at="message")
        if not self.ik_handle.hasAttr("world_scale_attr"):
            self.ik_handle.addAttr("world_scale_attr", at="float")
        if not self.ik_handle.hasAttr("prefix"):
            self.ik_handle.addAttr("prefix", dt="string")
        if not self.ik_handle.hasAttr("scale_power"):
            self.ik_handle.addAttr("scale_power", at="float")
        # set name prefix
        self._prefix = self.ik_handle.prefix.get() or self.ik_handle.name()
        self.ik_handle.visibility.set(False)
        # self.curve.visibility.set(False)

    def rebuild_curve(self, number_of_spans):
        pc.rebuildCurve(
            self.curve,
            s=number_of_spans,
            ch=0,
            rpo=1,
            rt=0,
            end=1,
            kr=0,
            kcp=0,
            kep=1,
            kt=0,
            d=3,
            tol=0.01,
        )

    def add_stretch(self):
        sel = pc.selected()
        curve_info, stretch_div_attr = create_curve_based_scale_setup(
            self.ik_handle, name=self.prefix
        )
        self.tag_node_and_connect(curve_info, "curve_info")
        stretch_div = stretch_div_attr.node()
        self.tag_node_and_connect(stretch_div, "stretch_div")
        # if curve was bound make set divisor to length of curveOrig!
        if self.skin_cluster:
            crv = self.curve.getParent()
            crv_shape = crv.getShape()
            shape_orig = [s for s in crv.getShapes() if s != crv_shape][0]
            stretch_div.input2X.set(get_curve_length(shape_orig))
        pc.select(sel)

    def remove_stretch(self):
        self.remove_volume()
        self.remove_world_scale()
        stretch_div = self.stretch_div
        if stretch_div:
            pc.delete(stretch_div)
            axis_map = {(1,0,0): "sx", (0,1,0): "sy", (0,0,1): "sz"}
            for jnt in self.joints:
                jnt.attr(axis_map[guess_forward_axis(jnt)]).set(1)

    def add_controllers(self, number_of_controls: int):
        # create the joints and controls
        joints = self.joints
        bind_joints = create_joint_controls_along_curve(
            self.curve, joints[0], number_of_controls, name=self.prefix
        )
        for i, jnt in enumerate(bind_joints):
            self.tag_node_and_connect(jnt, "control_joints")
            self.tag_node_and_connect(jnt.getParent(), "controls")
            jnt.addAttr("order", at="byte")
            jnt.order.set(i + 1)
            jnt.addAttr("dropoff_rate", at="float")
            jnt.dropoff_rate.set(self.initial_dropoff_rate)
        # orient first and last bind joint exactly to start and end joints
        pc.delete(
            pc.orientConstraint(
                joints[0], bind_joints[0].getParent().getParent().getParent()
            )
        )
        pc.delete(
            pc.orientConstraint(
                joints[-1], bind_joints[-1].getParent().getParent().getParent()
            )
        )
        setup_advanced_twist_control(self.ik_handle, bind_joints[0], bind_joints[-1])
        # finally bind the curve
        self.bind_curve()

    def remove_controllers(self, delete_parents: bool = True):
        self.unbind_curve()
        for ctrl in self.controls:
            offset_grp = ctrl.getParent()
            null_grp = None if not offset_grp else offset_grp.getParent()
            if ctrl.exists():
                pc.delete(ctrl)
            if delete_parents:
                if (
                    offset_grp
                    and offset_grp.exists()
                    and offset_grp.name().endswith("_offset_grp")
                ):
                    pc.delete(offset_grp)
                if (
                    null_grp
                    and null_grp.exists()
                    and null_grp.name().endswith("_null_grp")
                ):
                    pc.delete(null_grp)

    def bind_curve(self):
        sc = pc.skinCluster(
            *self.control_joints,
            self.curve,
            bindMethod=0,
            name=f"{self.prefix}_skinCluster",
            dropoffRate=self.initial_dropoff_rate,
        )
        self.tag_node_and_connect(sc, "skin_cluster")

    def unbind_curve(self):
        pc.delete(self.skin_cluster)

    def adjust_dropoff(self, jnt, dropoff_delta: float):
        val = max(0.1, min(jnt.dropoff_rate.get() + dropoff_delta, 10.0))
        jnt.dropoff_rate.set(val)
        pc.skinCluster(self.skin_cluster, e=True, inf=jnt, dropoffRate=val)

    def reset_dropoff(self):
        for jnt in self.control_joints:
            jnt.dropoff_rate.set(self.initial_dropoff_rate)
            pc.skinCluster(
                self.skin_cluster, e=True, inf=jnt, dr=self.initial_dropoff_rate
            )

    def add_volume(self):
        sel = pc.selected()
        setup_squash_stretch(self.ik_handle, self.scale_factor_attr, self.prefix)
        pc.select(sel)

    def remove_volume(self):
        exp = self.expression
        if exp:
            pc.delete(exp)
            axis_map = {(1,0,0): ("sy","sz"), (0,1,0): ("sx", "sz"), (0,0,1): ("sx", "sy")}
            for jnt in self.joints:
                fw_axis = guess_forward_axis(jnt)
                jnt.attr(axis_map[fw_axis][0]).set(1)
                jnt.attr(axis_map[fw_axis][1]).set(1)

    def add_world_scale(self, attr):
        sel = pc.selected()
        insert_normalized_scale_node(
            self.curve_info.attr("arcLength"), attr, name=self._prefix
        )
        attr >> self.ik_handle.world_scale_attr
        pc.select(sel)

    def remove_world_scale(self):
        wsd = self.world_scale_div
        if wsd:
            self.curve_info.arcLength >> self.stretch_div.input1X
            self.world_scale_attr // self.ik_handle.world_scale_attr
            pc.delete(wsd)

    def is_stretchy(self):
        crv = self.curve
        if not crv:
            return False
        return (
            True
            if crv.attr("worldSpace[0]").listConnections(type="curveInfo")
            else False
        )

    def is_volume_maintaining(self):
        return True if self.frame_caches else False

    def list_all_nodes(self):
        nodes = []
        for ctrl in self.controls:
            nodes.append(ctrl)
            if ctrl.getParent().name().endswith("_offset_grp"):
                nodes.append(ctrl.getParent())
            if ctrl.getParent().getParent().name().endswith("_null_grp"):
                nodes.append(ctrl.getParent().getParent())
        nodes.extend(self.control_joints)
        nodes.extend(self.frame_caches)
        if self.curve:
            nodes.append(self.curve)
        if self.curve_info:
            nodes.append(self.curve_info)
        if self.world_scale_div:
            nodes.append(self.world_scale_div)
        if self.stretch_div:
            nodes.append(self.stretch_div)
        if self.skin_cluster:
            nodes.append(self.skin_cluster)
        return nodes

    def tag_node(self, node: pc.nodetypes.DependNode):
        if not node.hasAttr(self._tag):
            node.addAttr(self._tag)

    def tag_node_and_connect(self, node: pc.nodetypes.DependNode, plug: str):
        self.tag_node(node)
        self.ik_handle.attr(plug) >> node.attr(self._tag)

    @property
    def frame_caches(self):
        return self.ik_handle.scale_power.listConnections(type="frameCache")

    @property
    def joints(self):
        return get_joint_list(self.ik_handle)

    @property
    def curve(self):
        return pc.PyNode(self.ik_handle.getCurve())

    @property
    def curve_info(self):
        crv_info = self.ik_handle.curve_info.listConnections(type="curveInfo")
        return None if not crv_info else crv_info[0]

    @property
    def controls(self):
        return self.ik_handle.controls.listConnections()

    @property
    def control_joints(self):
        return sorted(
            self.ik_handle.control_joints.listConnections(), key=lambda x: x.order.get()
        )

    @property
    def world_scale_attr(self):
        attrs = self.ik_handle.world_scale_attr.listConnections(plugs=True)
        return None if not attrs else attrs[0]

    @property
    def scale_factor_attr(self):
        div = self.stretch_div
        return None if not div else div.attr("outputX")

    @property
    def world_scale_object(self):
        wsa = self.world_scale_attr
        return None if not wsa else wsa.node()

    @property
    def world_scale_div(self):
        wsa = self.world_scale_attr
        if wsa:
            divs = wsa.listConnections(type="multiplyDivide")
            return None if not divs else divs[0]

    @property
    def stretch_div(self):
        divs = self.ik_handle.stretch_div.listConnections(type="multiplyDivide")
        return None if not divs else divs[0]

    @property
    def expression(self):
        sd = self.stretch_div
        expressions = sd.listConnections(type="expression")
        return None if not expressions else expressions[0]

    @property
    def skin_cluster(self):
        scs = self.ik_handle.skin_cluster.listConnections(type="skinCluster")
        return None if not scs else scs[0]

    @property
    def prefix(self):
        return self._prefix

    def change_prefix(self, name: str):
        for node in self.list_all_nodes():
            node.rename(node.name().replace(self.prefix, name))
        self.curve.rename(f"{name}_ik_crvShape")
        self.curve.getParent().rename(f"{name}_ik_crv")
        self.ik_handle.rename(f"{name}_ik_hndl")
        self._prefix = name
        self.ik_handle.prefix.set(name)
        self.ik_handle


class SplineIKManager:
    """The GUI Class for the management of a SplineIKRig."""

    def __init__(self):
        self.current_handle = None
        self.win_id = "spline_ik_window"
        self.w_btn = 30
        if pc.window(self.win_id, q=1, exists=1):
            pc.showWindow(self.win_id)
            return
        else:
            self.gui()

    def gui(self):
        window_width = 250
        window_height = 410

        if pc.window(self.win_id, q=1, exists=1):
            self.kill_script_jobs()
            pc.deleteUI(self.win_id)

        col1 = 1
        col2 = 100
        col3 = 60
        with pc.window(self.win_id, title="Spline IK Manager") as self.win:
            with pc.formLayout() as main_fl:
                with pc.columnLayout(adj=True, rs=5) as menu_cl:
                    with pc.optionMenu(cc=self.ik_menu_changed) as self.ik_menu:
                        pass
                with pc.columnLayout(adj=True, rs=5, enable=False) as self.edit_cl:
                    with pc.rowLayout(
                        nc=3, adj=1, cw3=(col1, col2, col3)
                    ) as self.name_rl:
                        pc.text(label="Prefix", align="left")
                        self.prefix_textField = pc.textField(
                            textChangedCommand=self.prefix_changed,
                            alwaysInvokeEnterCommandOnReturn=True,
                            ec=self.change_prefix,
                        )
                        self.change_prefix_button = pc.button(
                            label="Change", w=col3, enable=False, c=self.change_prefix
                        )
                    pc.separator(h=1)
                    with pc.rowLayout(
                        nc=3, adj=1, cw3=(col1, col2, col3)
                    ) as self.span_rl:
                        pc.text(label="Curve Spans", align="left")
                        self.spans_textField = pc.textField(
                            textChangedCommand=self.number_of_spans_changed,
                            alwaysInvokeEnterCommandOnReturn=True,
                            ec=self.change_number_of_spans,
                        )
                        self.spans_button = pc.button(
                            label="Change",
                            w=col3,
                            enable=False,
                            c=self.change_number_of_spans,
                        )
                    pc.separator(h=1)
                    with pc.rowLayout(
                        nc=3, adj=1, cw3=(col1, col2, col3)
                    ) as self.ctrl_count_rl:
                        pc.text(label="Controllers", align="left")
                        self.number_of_controls_textField = pc.textField(
                            textChangedCommand=self.number_of_controls_changed,
                            alwaysInvokeEnterCommandOnReturn=True,
                            ec=self.change_number_of_spans,
                            text="3",
                        )
                        self.number_of_controls_button = pc.button(
                            label="Create",
                            w=col3,
                            enable=False,
                            c=self.create_controllers,
                        )
                    pc.separator(h=1)
                    with pc.columnLayout(adj=True) as self.controls_cl:
                        with pc.rowLayout(
                            nc=2, cw2=(1, 2 * self.w_btn), cat=(2, "both", 0), adj=1
                        ):
                            pc.text(label="Joint", font="boldLabelFont", align="left")
                            pc.text(
                                label="Rigidity", font="boldLabelFont", align="center"
                            )
                        with pc.scrollLayout(
                            childResizable=True, bgc=(0.2, 0.2, 0.2), h=110
                        ):
                            with pc.columnLayout(
                                adj=True, visible=False, rs=2
                            ) as self.controls_list_cl:
                                pass
                        with pc.rowLayout(nc=2, cw2=(1, 2 * self.w_btn - 2), adj=1):
                            pc.text(label="")
                            pc.button(
                                label="Reset",
                                w=2 * self.w_btn,
                                c=pc.Callback(self.reset_dropoff),
                            )
                    pc.separator(h=1)
                    with pc.horizontalLayout():
                        self.stretchy_checkBox = pc.checkBox(
                            label="Stretchy", cc=self.toggle_stretchy
                        )
                        self.volume_checkBox = pc.checkBox(
                            label="Maintain Volume", cc=self.toggle_volume
                        )
                    pc.separator(h=1)
                    pc.text(label="World Scale Attribute", align="left")
                    with pc.rowLayout(nc=2, adj=1, cw2=(col1, col3)):
                        self.world_scale_textField = pc.textField(
                            pht="Select Attr in Channelbox and -->", editable=False
                        )
                        self.world_scale_button = pc.button(label="Set", w=col3)
                with pc.horizontalLayout() as buttons_hl:
                    pc.button(label="Close", c=pc.Callback(pc.deleteUI, self.win))

        for layout in [menu_cl, self.edit_cl, buttons_hl]:
            main_fl.attachForm(layout, "left", 5)
            main_fl.attachForm(layout, "right", 5)

        main_fl.attachForm(menu_cl, "top", 5)
        main_fl.attachForm(buttons_hl, "bottom", 5)
        main_fl.attachControl(self.edit_cl, "top", 0, menu_cl)
        main_fl.attachControl(self.edit_cl, "bottom", 0, buttons_hl)

        self.script_jobs = [
            pc.scriptJob(e=("DagObjectCreated", self.update_ik_menu)),
            pc.scriptJob(e=("NameChanged", self.update_ik_menu)),
            pc.scriptJob(e=("idleVeryLow", self.check_deletion_of_handle)),
        ]
        self.win.closeCommand(self.kill_script_jobs)
        self.win.setWidthHeight([window_width, window_height])
        self.update_ik_menu()

    def update_ik_menu(self, spline_ik_handles=None):
        self.ik_menu.deleteAllItems()
        current = ""
        pc.menuItem("Choose Spline IK from Dropdown ->", parent=self.ik_menu)
        spline_ik_handles = spline_ik_handles or self.list_spline_ik_handles()
        self.num_handles = len(spline_ik_handles)
        for spline_ik in spline_ik_handles:
            pc.menuItem(spline_ik.name(), parent=self.ik_menu)
            if self.current_handle and spline_ik == self.current_handle:
                current = spline_ik.name()
        if current:
            self.ik_menu.setValue(current)

    def list_spline_ik_handles(self):
        return [
            h
            for h in pc.ls(type="ikHandle")
            if type(h.ikSolver.get()) is pc.nodetypes.IkSplineSolver
        ]

    def ik_menu_changed(self, item):
        self.edit_cl.setEnable(False)
        handles = [h for h in self.list_spline_ik_handles() if h.name() == item]
        self.current_handle = None if not handles else handles[0]
        if self.current_handle:
            self.edit_cl.setEnable(True)
            self.rig = SplineIKRig(self.current_handle)
            self.prefix_textField.setText(self.rig.prefix)
            self.spans_textField.setText(self.rig.curve.spans.get())
            self.spans_button.setEnable(False)
            self.number_of_controls_textField.setText(len(self.rig.controls) or "3")
            self.number_of_controls_button.setLabel(
                "Change" if len(self.rig.controls) else "Create"
            )
            self.number_of_controls_button.setEnable(not len(self.rig.controls))
            self.update_controls_list()
            self.stretchy_checkBox.setValue(self.rig.is_stretchy())
            self.volume_checkBox.setValue(self.rig.is_volume_maintaining())
            wsa = self.rig.world_scale_attr
            if wsa:
                self.world_scale_textField.setText(wsa.name())
                self.world_scale_button.setLabel("Remove")
                self.world_scale_button.setCommand(self.remove_world_scale)
            else:
                self.world_scale_textField.setText("")
                self.world_scale_button.setLabel("Set")
                self.world_scale_button.setCommand(self.set_world_scale)

    def check_deletion_of_handle(self):
        spline_ik_handles = self.list_spline_ik_handles()
        if self.num_handles != len(spline_ik_handles):
            if self.current_handle not in spline_ik_handles:
                self.current_handle = None
            self.update_ik_menu()

    def update_controls_list(self):
        for child in self.controls_list_cl.getChildren():
            pc.deleteUI(child)
        if not self.rig.control_joints:
            return
        h_btn = 20
        dropoff_delta = 0.2
        for i, jnt in enumerate(self.rig.control_joints):
            if i != 0:
                pc.separator(h=1, parent=self.controls_list_cl)
            with pc.rowLayout(
                nc=3,
                cw3=(1, self.w_btn, self.w_btn),
                adj=1,
                parent=self.controls_list_cl,
            ):
                pc.text(label=jnt.name(), align="left")
                pc.button(
                    label="-",
                    w=self.w_btn,
                    h=h_btn,
                    c=pc.Callback(self.rig.adjust_dropoff, jnt, dropoff_delta),
                )
                pc.button(
                    label="+",
                    w=self.w_btn,
                    h=h_btn,
                    c=pc.Callback(self.rig.adjust_dropoff, jnt, -dropoff_delta),
                )
        self.controls_list_cl.setVisible(True)

    def prefix_changed(self, name):
        self.change_prefix_button.setEnable(name != self.rig.prefix)

    def change_prefix(self, *args):
        name = self.prefix_textField.getText()
        if name:
            self.rig.change_prefix(name)
        self.change_prefix_button.setEnable(False)

    def number_of_spans_changed(self, num_string):
        num_string = "".join([c for c in num_string if c.isdigit()])
        if not num_string:
            self.spans_button.setEnable(False)
            return
        num = int(num_string)
        if num > 2 and num != self.rig.curve.spans.get():
            self.spans_button.setEnable(True)

    def change_number_of_spans(self, *args):
        num = int(self.spans_textField.getText())
        num_ctrls = 0
        if num > 2:
            if num == self.rig.curve.spans.get():
                return
            if self.rig.skin_cluster:
                ok = pc.confirmBox(
                    "Warning!",
                    "Spline is already bound!\nTo change the number of spans the binding and controls have to be deleted.\nContinue anyway?",
                )
                if not ok:
                    return
                num_ctrls = len(self.rig.controls)
                self.rig.remove_controllers()
            self.rig.rebuild_curve(num)
            pc.delete(self.rig.curve, ch=True)
            if num_ctrls:
                self.rig.add_controllers(num_ctrls)
                self.update_controls_list()
        self.spans_button.setEnable(False)

    def number_of_controls_changed(self, num_string):
        num_string = "".join([c for c in num_string if c.isdigit()])
        if not num_string:
            self.number_of_controls_button.setEnable(False)
            return
        num = int(num_string)
        if num >= 2 and num != len(self.rig.controls):
            self.number_of_controls_button.setEnable(True)

    def create_controllers(self, *args):
        num = self.number_of_controls_textField.getText()
        if not num:
            return
        num = int(num)
        if self.rig.skin_cluster:
            ok = pc.confirmBox(
                "Warning!",
                "Spline is already bound!\nChanging the number of controls will delete the current bind.\nAll weight edits will be lost.\nContinue anyway?",
            )
            if not ok:
                return
            self.rig.remove_controllers()
        self.rig.add_controllers(num)
        self.number_of_controls_button.setLabel("Change")
        self.number_of_controls_button.setEnable(False)
        self.update_controls_list()

    def reset_dropoff(self, *args):
        self.rig.reset_dropoff()

    def toggle_stretchy(self, checked):
        if checked:
            self.rig.add_stretch()
            self.volume_checkBox.setEnable(True)
            self.world_scale_button.setEnable(True)
        else:
            self.rig.remove_stretch()
            self.volume_checkBox.setValue(False)
            self.volume_checkBox.setEnable(False)
            self.world_scale_textField.setText("")
            self.world_scale_button.setLabel("Set")
            self.world_scale_button.setCommand(self.set_world_scale)
            self.world_scale_button.setEnable(False)

    def toggle_volume(self, checked):
        if checked:
            self.rig.add_volume()
        else:
            self.rig.remove_volume()

    def set_world_scale(self, *args):
        attrs = get_selected_channelbox_attributes()
        if not attrs:
            pc.warning("Please select exactly one attribute name in the Channel Box.")
            return
        attr = pc.selected()[0].attr(attrs[0])
        self.world_scale_textField.setText(attr.name())
        self.rig.add_world_scale(attr)
        self.world_scale_button.setLabel("Remove")
        self.world_scale_button.setCommand(self.remove_world_scale)

    def remove_world_scale(self, *args):
        self.rig.remove_world_scale()
        self.world_scale_textField.setText("")
        self.world_scale_button.setLabel("Set")
        self.world_scale_button.setCommand(self.set_world_scale)

    def kill_script_jobs(self, *args):
        for job in self.script_jobs:
            pc.scriptJob(kill=job, force=True)


# sread weights to influences currently on ZERO
# interesting but needs work
# jnt = sm.rig.control_joints[-1]


# def get_weights_for(jnt):
#     sel_set, influences = sm.rig.skin_cluster.getPointsAffectedByInfluence(jnt)
#     cvs = sel_set[0]
#     weight_map = {}
#     for cv, inf in zip(cvs, influences):
#         weight_map[cv.index()] = inf

#     weights = []
#     for i in range(sm.rig.curve.numCVs()):
#         weights.append(weight_map.get(i, 0))
#     return weights


# def spread_weights_for(jnt, spread_to_zero_weights=0.15, up_existing_weights=0.05):
#     new_weights = []
#     for i, weight in enumerate(get_weights_for(jnt)):
#         if weight > 0.99:
#             new_weights.append(weight)
#             continue
#         left_weight = weights[i if i == 0 else i - 1]
#         right_weight = weights[i if i == len(weights) - 1 else i + 1]
#         max_weight = max((left_weight, right_weight))
#         if weight != 0:
#             new_weights.append(weight * (1.0 + up_existing_weights))
#         elif max_weight != 0:
#             new_weights.append(max_weight * spread_to_zero_weights)
#         else:
#             new_weights.append(weight)
#     for i, weight in enumerate(new_weights):
#         pc.skinPercent(sm.rig.skin_cluster,
#                        sm.rig.curve.cv[i], tv=(jnt, weight))


# spread_weights_for(jnt)
