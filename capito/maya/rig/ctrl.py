import pymel.core as pc

from capito.maya.util.names import legalize_text, get_legal_character
from capito.maya.geo.shapes import get_symmetry_dict
from capito.maya.rig.deformers import (
    get_soft_selection_values,
    create_soft_cluster,
    edit_soft_cluster_weights,
    list_inputs_of_type,
    duplicate_orig_shape,
    get_orig_shape,
    get_visible_shape
)


def slider_control(name, two_sided=True):
    min_val = -1 if two_sided else 0
    # build square
    rect = pc.curve(
        n="{}_frame_crv".format(name),
        d=1,
        p=[
            (-0.1, min_val, 0),
            (0.1, min_val, 0),
            (0.1, 1, 0),
            (-0.1, 1, 0),
            (-0.1, min_val, 0),
        ],
        k=[0, 1, 2, 3, 4],
    )
    rect_shape = rect.getShape()
    # set shape  to referenzed display mode
    rect_shape.overrideEnabled.set(True)
    rect_shape.setAttr("overrideDisplayType", 2)

    # the ctrl-circle
    ctrl = pc.circle(n="{}_ctrl".format(name), r=0.15)[0]
    # set limits
    pc.transformLimits(ctrl, tx=(0, 0), etx=(1, 1))
    pc.transformLimits(ctrl, ty=(min_val, 1), ety=(1, 1))
    pc.transformLimits(ctrl, tz=(0, 0), etz=(1, 1))
    # lock, hide and add attributes
    for attr in ("tx", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
        ctrl.setAttr(attr, keyable=False, lock=True, channelBox=False)

    pc.addAttr(ctrl, ln="val1", r=True, hidden=False, at="double", min=0, max=1, dv=0)
    if two_sided:
        pc.addAttr(
            ctrl, ln="val2", r=True, hidden=False, at="double", min=0, max=1, dv=0
        )
    # build expression
    expressionString = "{0}.val1 = clamp( 0, 1, {0}.ty );".format(ctrl)
    if two_sided:
        expressionString += "\n{0}.val2 = -1 * clamp( -1, 0, {0}.ty );".format(ctrl)
    # set expression
    pc.expression(o=ctrl, s=expressionString, n="{}_expression".format(ctrl))
    # parent
    pc.parent(ctrl, rect)
    return ctrl


def four_corner_control(name):
    # build square
    rect = pc.curve(
        n="{}_frame_crv".format(name),
        d=1,
        p=[(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0), (-1, -1, 0)],
        k=[0, 1, 2, 3, 4],
    )
    rect_shape = rect.getShape()
    # set shape  to referenzed display mode
    rect_shape.overrideEnabled.set(True)
    rect_shape.setAttr("overrideDisplayType", 2)

    # the ctrl-circle
    ctrl = pc.circle(n="{}_ctrl".format(name), r=0.15)[0]
    # set limits
    pc.transformLimits(ctrl, tx=(-1, 1), etx=(1, 1))
    pc.transformLimits(ctrl, ty=(-1, 1), ety=(1, 1))
    pc.transformLimits(ctrl, tz=(0, 0), etz=(1, 1))
    # lock, hide and add attributes
    for attr in ["tz", "rx", "ry", "rz", "sx", "sy", "sz"]:
        ctrl.setAttr(attr, keyable=False, lock=True, channelBox=False)

    for attr in ["topLeftVal", "topRightVal", "bottomLeftVal", "bottomRightVal"]:
        pc.addAttr(ctrl, ln=attr, r=True, at="double", min=0, max=1, dv=0, keyable=True)

    # build expression
    expressionString = """
        {0}.topLeftVal = clamp( 0,1,{0}.translateY * (1 + clamp( -1,0,{0}.translateX ) ) );
        {0}.topRightVal = clamp( 0,1,{0}.translateY * (1 - clamp( 0,1,{0}.translateX ) ) );
        {0}.bottomRightVal = clamp( 0,1,-{0}.translateY * (1 - clamp( 0,1,{0}.translateX ) ) );
        {0}.bottomLeftVal = clamp( 0,1,-{0}.translateY * (1 + clamp( -1,0,{0}.translateX ) ) );
        """.format(
        ctrl
    )
    # set expression
    pc.expression(o=ctrl, s=expressionString, n="{}_expression".format(ctrl))
    # parent
    pc.parent(ctrl, rect)
    return ctrl


# def create_mirrored_sticky_control(ctrl, name, mirror_matrix=[-1, 1, 1]):
#     input_pin = ctrl.getParent().getParent().getSiblings()[0]
#     input_pin_pos = [
#         v*s for v, s in zip(input_pin.getTranslation(space="world"), mirror_matrix)
#     ]

#     cluster_handle = ctrl.attr(
#         "translate").listConnections(type="transform")[0]
#     cluster = cluster_handle.attr(
#         "worldMatrix").listConnections(type="cluster")[0]
#     cluster_set = pc.listConnections(cluster, type="objectSet")[0]
#     pc.select(cluster_set.flattened())
#     verts = pc.selected(fl=True)

#     transform = get_sticky_transform(
#         ctrl.getParent().getParent().getParent().getParent())

#     weight_dict = []
#     for vert in verts:
#         pc.select(vert, symmetry=True)
#         sym_verts = [v for v in pc.selected() if v != vert]
#         sym_vert = vert if not sym_verts else sym_verts[0]
#         weight_dict.append(
#             (sym_vert.index(), pc.percent(cluster, vert, q=True, v=True)[0])
#         )

#     constraints = ctrl.getParent().getSiblings(type="orientConstraint")
#     orient_con = None if not constraints else constraints[0]
#     orient_to = None
#     if orient_con:
#         orient_to = orient_con.attr(
#             "target[0].targetParentMatrix").listConnections()[0]

#     create_sticky_control(
#         name=name, transform=transform, bs_node=None, orient_to=orient_to,
#         weight_dict=weight_dict, input_pin_pos=input_pin_pos
#     )


class BlendShapePrompt:
    """A helper class for asking the user for the correct BlendShape Node
    in the process of creating a StickyControlManager Setup.
    """

    def __init__(self, transform, callback):
        self.NEW_BS_TEXT = "New Blendshape Node"
        self.window_name = "blendshape_adder_win"
        self.window_title = f"Add BlendShape to {transform.name()}"
        self.padding = 5

        self.transform = transform
        self.callback = callback

        self.bs_dict = {}

        self.gui()
        self.win.setWidthHeight((385, 145))

    def gui(self):
        if pc.window(self.window_name, exists=True):
            pc.deleteUI(self.window_name)

        with pc.window(self.window_name, title=self.window_title) as self.win:
            with pc.formLayout(numberOfDivisions=100) as self.main_fl:
                with pc.scrollLayout(
                    childResizable=True, vsb=False
                ) as self.top_container:
                    with pc.columnLayout(adj=True):
                        pc.text(
                            label="Please specify where to add the BS-Target",
                            align="left",
                            font="boldLabelFont",
                        )
                        pc.separator(h=10)
                        with pc.optionMenuGrp(
                            label="Add Target to:", cw2=(90, 90), adj=2
                        ) as self.bs_optionMenuGrp:
                            for bs in list_inputs_of_type(
                                self.transform, pc.nodetypes.BlendShape
                            ):
                                pc.menuItem(label=bs.name())
                                self.bs_dict[bs.name()] = bs
                            pc.menuItem(label=self.NEW_BS_TEXT)
                with pc.columnLayout(adj=True) as self.bottom_container:
                    with pc.horizontalLayout():
                        pc.button(label="OK", c=self.ok)
                        pc.button(label="Cancel", c=self.cancel)

        self.main_fl.attachForm(self.top_container, "top", self.padding)
        self.main_fl.attachForm(self.top_container, "left", self.padding)
        self.main_fl.attachForm(self.top_container, "right", self.padding)
        self.main_fl.attachForm(self.bottom_container, "left", self.padding)
        self.main_fl.attachForm(self.bottom_container, "right", self.padding)
        self.main_fl.attachForm(self.bottom_container, "bottom", self.padding)
        self.main_fl.attachControl(
            self.top_container, "bottom", self.padding, self.bottom_container
        )
        self.main_fl.attachNone(self.bottom_container, "top")

    def ok(self, *args):
        selected_item = self.bs_optionMenuGrp.getValue()
        bs_node = self.bs_dict.get(selected_item, None)
        if bs_node is None:
            pc.select(self.transform)
            bs_node = pc.blendShape(automatic=True)[0]
        self.callback(bs_node)
        pc.deleteUI(self.win)

    def cancel(self, *args):
        self.callback()
        pc.deleteUI(self.win)


GRP = "sticky_grp"
TRANS = "sticky_transform"
VIS = "sticky_controler_visibility"
BS_TRANS = "sticky_blendshape_transform"
BS_NODE = "sticky_blendshape_node"
BS_INDEX = "sticky_bs_index"
PROX = "sticky_proximitypin"
CTRLS = "sticky_controls"
STD_ORIENT = "orient_object"


class StickyControlManager:
    def __init__(self, group=None):
        self.symmetry_matrices = {"x": [-1, 1, 1], "y": [1, -1, 1], "z": [1, 1, -1]}
        if group:
            self.grp = group
            self.init_class_attributes()

    def create(
        self,
        transform,
        name="sticky",
        offset_translate=1.0,
        offset_orient=1.0,
        callback=None,
        callback_manager_list=None,
    ):
        self.transform, self.name = transform, name
        self.offset_translate, self.offset_orient = offset_translate, offset_orient
        self.callback = callback
        self.callback_manager_list = callback_manager_list or []
        self.create_grp()
        self.create_attributes()
        self.start_setup()
        return self

    def create_grp(self):
        self.grp = pc.group(empty=True, n=f"{self.name}_grp")
        self.name = self.grp.name()
        for channel in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]:
            self.grp.attr(channel).setKeyable(False)
            self.grp.attr(channel).setLocked(False)

    def create_attributes(self):
        self.grp.addAttr(VIS, at="bool", dv=1)
        self.grp.addAttr(BS_TRANS, at="message")
        self.grp.addAttr(BS_NODE, at="message")
        self.grp.addAttr(BS_INDEX, at="short")
        self.grp.addAttr(PROX, at="message")
        self.grp.addAttr(TRANS, at="message")
        self.grp.addAttr(CTRLS, at="message")
        self.grp.addAttr(STD_ORIENT, at="message")
        if not self.transform.hasAttr(GRP):
            self.transform.addAttr(GRP, at="message", dv=1)
        self.transform.attr(GRP) >> self.grp.attr(TRANS)
        self.grp.addAttr("search", dt="string")
        self.grp.attr("search").set("l_")
        self.grp.addAttr("replace", dt="string")
        self.grp.attr("replace").set("r_")
        self.grp.addAttr("symmetry_direction", dt="string")
        self.grp.attr("symmetry_direction").set("x")

    def start_setup(self):
        bs_nodes = list_inputs_of_type(self.transform, pc.nodetypes.BlendShape)
        if not bs_nodes:
            pc.select(self.transform)
            bs_node = pc.blendShape(automatic=True)[0]
            self.blendshape_setup(bs_node)
        else:
            BlendShapePrompt(self.transform, self.blendshape_setup)

    def blendshape_setup(self, bs_node=None):
        if bs_node is None:
            pc.warning("Unable to setup BlendShape. Aborting.")
            return
        #bs_node.rename(f"{self.name}_bs")

        index_list = bs_node.weightIndexList()
        index = 0 if not index_list else index_list[-1] + 1

        bs_transform = duplicate_orig_shape(self.transform)
        bs_transform.rename(f"{self.name}_bs_geo")
        print("298 bs_transform", bs_transform)
        bs_node.addTarget(
            baseObject=get_visible_shape(self.transform),
            fullWeight=1.0,
            targetType="object",
            weightIndex=index,
            newTarget=bs_transform.getShape(),
        )

        if not bs_node.hasAttr(self.grp.name()):
            bs_node.addAttr(self.grp.name(), at="message")
        self.grp.attr(BS_NODE) >> bs_node.attr(self.grp.name())

        if not bs_transform.hasAttr(GRP):
            bs_transform.addAttr(GRP, at="message")
        self.grp.attr(BS_TRANS) >> bs_transform.attr(GRP)

        name = self.name
        i = 1
        while bs_node.hasAttr(name):
            name = f"{self.name}_{i}"
            i += 1
        pc.aliasAttr(name, f"{bs_node.name()}.w[{index}]")
        bs_node.setAttr(f"weight[{index}]", 1)
        self.grp.attr(BS_INDEX).set(index)
        bs_transform.hide()
        pc.parent(bs_transform, self.grp)

        self.proxpin_setup()

    def proxpin_setup(self):
        proxpin = pc.createNode("proximityPin")
        proxpin.rename(f"{self.name}_prox")
        proxpin.offsetOrientation.set(1)
        orig_shape = get_orig_shape(self.transform)
        orig_shape.outMesh >> proxpin.originalGeometry
        get_visible_shape(self.transform).worldMesh >> proxpin.deformedGeometry
        if not proxpin.hasAttr(GRP):
            proxpin.addAttr(GRP, at="bool")
        self.grp.attr(PROX) >> proxpin.attr(GRP)
        self.init_class_attributes()
        if self.callback:
            self.callback_manager_list.append(self)
            self.callback(self.callback_manager_list, self)

    def init_class_attributes(self):
        self.transform = self.grp.attr(TRANS).listConnections()[0]
        self.bs_transform = self.grp.attr(BS_TRANS).listConnections()[0]
        self.bs_node = self.grp.attr(BS_NODE).listConnections()[0]
        self.bs_index = self.grp.getAttr(BS_INDEX)
        self.prox_node = self.grp.attr(PROX).listConnections()[0]
        self.controls_channel = self.grp.attr(CTRLS)
        self.controler_visibility = self.grp.attr(VIS)
        self.name = self.grp.name().split("|")[-1]
        std_orient = self.grp.attr(STD_ORIENT).listConnections()
        self.orient_object = None if not std_orient else std_orient[0]

    def set_orient_object(self, obj):
        obj.visibility >> self.grp.attr(STD_ORIENT)
        self.orient_object = obj

    def clear_orient_object(self):
        self.orient_object.visibility // self.grp.attr(STD_ORIENT)
        self.orient_object = None

    def __eq__(self, other):
        if isinstance(other, StickyControlManager):
            return self.grp == other.grp
        return False

    @property
    def symmetry_matrix(self):
        return self.symmetry_matrices[self.grp.symmetry_direction.get()]

    @property
    def controls(self):
        return sorted(self.grp.attr(CTRLS).listConnections(), key=lambda x: x.name())


class StickyControl:
    def __init__(
        self,
        name=None,
        manager=None,
        ctrl=None,
        weight_dict=None,
        orient_to=None,
        initial_pin_pos=None,
        connect_translate=True,
        connect_rotate=True,
        connect_scale=True,
    ):
        if ctrl is None:
            self.create(
                name=name or "sticky",
                manager=manager,
                weight_dict=weight_dict,
                orient_to=orient_to,
                initial_pin_pos=initial_pin_pos,
                connect_translate=connect_translate,
                connect_rotate=connect_rotate,
                connect_scale=connect_scale,
            )
        else:
            self.init_from_ctrl(ctrl)

    def init_from_ctrl(self, ctrl):
        self.ctrl = ctrl
        self.manager = StickyControlManager(ctrl.attr(GRP).listConnections()[-1])

    def create(
        self,
        name=None,
        manager=None,
        weight_dict=None,
        orient_to=None,
        initial_pin_pos=None,
        connect_translate=True,
        connect_rotate=True,
        connect_scale=True,
    ):
        self.manager = manager

        if weight_dict is None:
            weight_dict = get_soft_selection_values()

        if initial_pin_pos is None:
            vtx = pc.selected()[0]
            initial_pin_pos = [0, 0, 0] if not vtx else vtx.getPosition(space="world")

        ctrl_grp = pc.group(empty=True, n=f"{name}_ctrl_grp")
        self.manager.controler_visibility >> ctrl_grp.visibility
        pc.parent(ctrl_grp, self.manager.grp)

        cluster_handle = create_soft_cluster(
            name=name,
            shape=self.manager.bs_transform.getShape(),
            weight_dict=weight_dict,
        )
        cluster_handle.hide()
        cluster = cluster_handle.attr("worldMatrix[0]").listConnections()[0]
        pc.parent(cluster_handle, self.manager.grp)

        input_pin = pc.group(empty=True, n=f"{name}_input_pin")
        pc.parent(input_pin, ctrl_grp)
        output_pin = pc.group(empty=True, n=f"{name}_output_pin")
        pc.parent(output_pin, ctrl_grp)
        if orient_to:
            pc.orientConstraint(orient_to, output_pin, maintainOffset=True)

        input_pin.setTranslation(initial_pin_pos, space="world")

        indices = self.manager.prox_node.attr("inputMatrix").getArrayIndices()
        i = 0 if not indices else max(indices) + 1
        input_pin.matrix >> self.manager.prox_node.attr("inputMatrix[{}]".format(i))
        (
            self.manager.prox_node.attr(f"outputMatrix[{i}]")
            >> output_pin.offsetParentMatrix
        )

        offset_grp = pc.group(empty=True, n=f"{name}_offset_grp")
        ctrl = pc.circle(radius=0.2)[0]
        ctrl.rename(name)
        pc.delete(ctrl, ch=True)
        pc.parent(offset_grp, output_pin)
        pc.parent(ctrl, offset_grp)
        ctrl.addAttr("sticky_grp", at="message")
        ctrl.addAttr("symmetry_control", at="message")
        ctrl.addAttr("proximity_pin_index", at="short")
        ctrl.setAttr("proximity_pin_index", i)
        self.manager.controls_channel >> ctrl.sticky_grp

        neg_mult = pc.createNode("multiplyDivide", n=f"{name}_neg_mult")

        neg_mult.setAttr("input2", [-1, -1, -1])
        ctrl.translate >> neg_mult.input1
        neg_mult.output >> offset_grp.translate
        if connect_translate:
            ctrl.translate >> cluster_handle.translate
        if connect_rotate:
            ctrl.rotate >> cluster_handle.rotate
        if connect_scale:
            ctrl.scale >> cluster_handle.scale

        self.ctrl = ctrl
        connection_list = (
            (cluster_handle, "cluster_handle"),
            (cluster, "cluster"),
            (output_pin, "output_pin"),
            (input_pin, "input_pin"),
        )
        for node, attr in connection_list:
            self.ctrl.addAttr(attr, at="message")
            node.addAttr("ctrl", at="message")
            self.ctrl.attr(attr) >> node.ctrl

        pc.select(self.ctrl)

    def edit_weights(self, weight_dict=None):
        edit_soft_cluster_weights(self.cluster_handle, weight_dict)

    def is_connected(self, channel):
        """channel must be "t", "r" or "s" """
        return pc.isConnected(
            self.ctrl.attr(channel), self.cluster_handle.attr(channel)
        )

    def connection_array(self):
        return (self.is_connected("t"), self.is_connected("r"), self.is_connected("s"))

    def connect(self, channel):
        """channel must be "t", "r" or "s" """
        self.ctrl.attr(channel) >> self.cluster_handle.attr(channel)

    def disconnect(self, channel):
        """channel must be "t", "r" or "s" """
        self.ctrl.attr(channel) // self.cluster_handle.attr(channel)
        self.cluster_handle.attr(channel).set(
            (1, 1, 1) if channel == "s" else (0, 0, 0)
        )

    def set_orient_object(self, obj=None):
        if self.orient_object_constraint:
            pc.delete(self.orient_object_constraint)
        if obj:
            pc.orientConstraint(obj, self.output_pin, maintainOffset=True)

    def get_symmetry_weights(self, weight_threshold=0.001):
        weights = {}
        for i, w in enumerate(self.cluster.attr("weightList[0].weights").get()):
            if w > weight_threshold:
                weights[i] = w

        sym_status = pc.symmetricModelling(q=True, symmetry=True)
        pc.symmetricModelling(symmetry=True)
        sym_weights = {}
        for i, w in weights.items():
            pc.select(self.manager.transform.vtx[i], symmetry=True)
            pair = [v.index() for v in pc.selected()]
            if len(pair) == 1:
                j = i
            else:
                j = [v for v in pair if v != i][0]
            sym_weights[j] = w
        pc.symmetricModelling(symmetry=sym_status)
        return sym_weights

    def create_symmetry_control(self, name, sym_matrix=None):
        sym_matrix = sym_matrix or [-1, 1, 1]
        sym_pin_pos = [
            v * m for v, m in zip(self.ctrl.getTranslation(space="world"), sym_matrix)
        ]
        sc = StickyControl(
            name,
            self.manager,
            orient_to=self.orient_object,
            initial_pin_pos=sym_pin_pos,
            weight_dict=self.get_symmetry_weights(),
        )
        self.ctrl.symmetry_control >> sc.ctrl.symmetry_control

    def push_weights_to_symmetry_controller(self):
        self.symmetry_control.edit_weights(self.get_symmetry_weights())

    def remove_symmetry_control(self):
        sc = self.symmetry_control
        if sc:
            if pc.isConnected(self.ctrl.symmetry_control, sc.ctrl.symmetry_control):
                self.ctrl.symmetry_control // sc.ctrl.symmetry_control
            else:
                sc.ctrl.symmetry_control // self.ctrl.symmetry_control

    def delete(self):
        self.output_pin.offsetParentMatrix.disconnect()
        self.input_pin.matrix.disconnect()
        pc.delete(self.cluster_handle)
        pc.delete(self.input_pin.getParent())

    @property
    def cluster(self):
        return self.ctrl.attr("cluster").listConnections()[0]

    @property
    def cluster_handle(self):
        return self.ctrl.attr("cluster_handle").listConnections()[0]

    @property
    def input_pin(self):
        return self.ctrl.attr("input_pin").listConnections()[0]

    @property
    def output_pin(self):
        return self.ctrl.attr("output_pin").listConnections()[0]

    @property
    def symmetry_control(self):
        ctrls = self.ctrl.attr("symmetry_control").listConnections()
        if ctrls:
            return StickyControl(ctrl=ctrls[0])
        return None

    @property
    def orient_object(self):
        ocs = self.output_pin.listRelatives(children=True, type="orientConstraint")
        return (
            None
            if not ocs
            else ocs[0].attr("target[0].targetRotate").listConnections()[0]
        )

    @property
    def orient_object_constraint(self):
        ocs = self.output_pin.listRelatives(children=True, type="orientConstraint")
        return None if not ocs else ocs[0]

    @property
    def name(self):
        return self.ctrl.name().split("|")[-1]


def get_sticky_managers(transform):
    managers = []
    if transform.hasAttr(GRP):
        grps = transform.attr(GRP).listConnections()
        for grp in grps:
            managers.append(StickyControlManager(grp))
    return managers


def is_sticky_controler(transform):
    return transform.hasAttr(GRP)


class StickyControllers:
    def __init__(self):
        self.win_id = "sticky_ctrl_window"
        self.manager = None
        self.current_controls = []
        if pc.window(self.win_id, q=1, exists=1):
            pc.showWindow(self.win_id)
            return
        else:
            self.gui()

    def gui(self):
        window_width = 400
        window_height = 500
        p = 5
        cw1 = 100
        scrollbar_thickness = 10
        self.reweight_w = 50
        self.del_w = 30
        self.cw6 = [1, 80, 75, 55, self.reweight_w, self.del_w]
        self.cw6_h = self.cw6[:]
        self.cw6_h[-1] += scrollbar_thickness
        self.trs_cws = (1, 15, 15, 15)

        if pc.window(self.win_id, q=1, exists=1):
            self.kill_script_jobs()
            pc.deleteUI(self.win_id)

        with pc.window(self.win_id, title="Sticky Controls") as self.win:
            with pc.formLayout() as form_layout:
                with pc.columnLayout(adj=True) as self.manager_select_cl:
                    with pc.rowLayout(nc=2, adj=1):
                        with pc.optionMenu(
                            h=20, cc=self.manager_selected
                        ) as self.manager_option_menu:
                            pass
                        pc.button("Add Sticky Setup", h=20, c=self.add_sticky_setup)
                    pc.separator(h=10)
                with pc.columnLayout(adj=True) as self.manager_attributes_cl:
                    with pc.rowLayout(nc=3, cw3=(cw1, 1, 80), adj=2):
                        pc.text(label="Std Orient Object")
                        self.std_orient_tf = pc.textField(
                            pht="MMB Drop Object",
                            text="",
                            editable=True,
                            tcc=pc.Callback(self.set_manager_orient_object),
                        )
                        self.std_orient_button = pc.button(
                            label="Clear",
                            c=self.clear_manager_orient_object,
                            enable=False,
                        )
                    # TODO: Symmetry Options: Search/Replace and Mirror-Axis
                    pc.separator(h=10)
                with pc.formLayout() as self.controllers_fl:
                    with pc.columnLayout(adj=True) as self.controller_add_cl:
                        with pc.rowLayout(nc=5, cw5=(cw1, 90, 80, 60, 1), adj=5):
                            pc.text(label="Symmetry Options")
                            self.search_tfg = pc.textFieldGrp(
                                label="Replace: ",
                                cw2=(45, 40),
                                text="l_",
                                tcc=self.set_search_string,
                            )
                            self.replace_tfg = pc.textFieldGrp(
                                label="with: ",
                                cw2=(33, 40),
                                text="r_",
                                tcc=self.set_replace_string,
                            )
                            pc.text(label="Direction:")
                            with pc.optionMenu(
                                cc=self.set_symmetry_direction
                            ) as self.symmetry_direction_menu:
                                pc.menuItem("x")
                                pc.menuItem("y")
                                pc.menuItem("z")

                        pc.separator(h=10)
                        pc.iconTextButton(
                            style="iconAndTextHorizontal",
                            i="addCreateGeneric.png",
                            label="Add Controller",
                            h=20,
                            c=self.add_controller,
                        )
                    with pc.scrollLayout(cr=True, h=27) as self.controller_header_sl:
                        with pc.rowLayout(nc=6, cw6=self.cw6_h, adj=1):
                            pc.checkBox(label="Name", cc=self.select_all)
                            pc.text(label="Orient", al="left")
                            pc.text(label="Symmetry", al="left")
                            with pc.rowLayout(nc=4, cw4=self.trs_cws):
                                pc.text(label="")
                                pc.text(label="T", al="center")
                                pc.text(label="R", al="center")
                                pc.text(label="S", al="center")
                            pc.text(label="", w=self.reweight_w)
                            pc.text(label="", w=self.del_w + scrollbar_thickness)
                    with pc.scrollLayout(
                        cr=True, bgc=(0.2, 0.2, 0.2), vsb=True, vst=scrollbar_thickness
                    ) as controller_sl:
                        with pc.columnLayout(adj=True) as self.controller_list_cl:
                            pass
                    with pc.rowLayout(nc=3) as self.actions_rl:
                        pc.text(label="Action for Selected:", h=20)
                        with pc.optionMenu(h=20) as self.controller_action_menu:
                            pc.menuItem(label="Orient to Std. Object")
                            pc.menuItem(label="Clear Orient Object")
                            pc.menuItem(label="Delete")
                        pc.button("Go", h=20, c=self.batch_action)

        # adjust form attachments for controller area
        for c in (
            self.controller_add_cl,
            self.controller_header_sl,
            controller_sl,
            self.actions_rl,
        ):
            self.controllers_fl.attachForm(c, "left", 0)
            self.controllers_fl.attachForm(c, "right", 0)
        self.controllers_fl.attachForm(self.controller_add_cl, "top", 0)
        self.controllers_fl.attachForm(self.actions_rl, "bottom", 0)

        self.controllers_fl.attachControl(
            self.controller_header_sl, "top", 0, self.controller_add_cl
        )
        self.controllers_fl.attachControl(
            controller_sl, "top", 0, self.controller_header_sl
        )
        self.controllers_fl.attachControl(controller_sl, "bottom", 0, self.actions_rl)

        # adjust form attachment for overall layout
        for c in (
            self.manager_select_cl,
            self.manager_attributes_cl,
            self.controllers_fl,
        ):
            form_layout.attachForm(c, "left", p)
            form_layout.attachForm(c, "right", p)
        form_layout.attachForm(self.manager_select_cl, "top", p)
        form_layout.attachForm(self.controllers_fl, "bottom", p)
        form_layout.attachControl(
            self.manager_attributes_cl, "top", p, self.manager_select_cl
        )
        form_layout.attachControl(
            self.controllers_fl, "top", p, self.manager_attributes_cl
        )

        self.enable_manager_layouts(False)
        self.enable_controllers_layouts(False)

        self.script_jobs = [
            pc.scriptJob(e=("SelectionChanged", self.on_selection_changed))
        ]
        self.win.closeCommand(self.kill_script_jobs)
        self.win.setWidthHeight([window_width, window_height])
        self.on_selection_changed()

    def on_selection_changed(self):
        """check what has to be updated in the gui"""
        sel = pc.selected()
        if not sel:
            return
        obj = sel[0]
        if self.manager and not pc.objExists(self.manager.transform):
            self.manager = None
            self.reset_gui()
            return
        if not isinstance(obj, pc.nodetypes.Transform):
            return
        shape = obj.getShape()
        if not shape:
            return
        if isinstance(shape, pc.nodetypes.Mesh):
            managers = get_sticky_managers(obj)
            if self.manager in managers:  # gui showing already the correct things
                return
            else:  # complete gui update
                self.update_gui(managers, None if not managers else managers[0])
                return
        elif is_sticky_controler(obj):
            controler = StickyControl(ctrl=obj)
            if not self.manager == controler.manager:
                self.update_gui(
                    get_sticky_managers(controler.manager.transform), controler.manager
                )
            self.select_controller_checkbox(controler)

    def update_gui(self, managers, selected_manager):
        self.manager = selected_manager
        self.manager_option_menu.deleteAllItems()
        self.manager_option_menu.addItems([m.name for m in managers])
        if selected_manager:
            self.manager_option_menu.setValue(selected_manager.name)

        if managers:
            self.enable_manager_layouts(True)

        self.enable_controllers_layouts(False)
        self.update_manager_orient_object_gui()
        if self.manager:
            if self.manager.controls:
                self.enable_controllers_layouts(True)
            s = self.manager.grp.attr("search").get()
            self.search_tfg.setText("l_" if not s else s)
            r = self.manager.grp.attr("replace").get()
            self.replace_tfg.setText("r_" if not r else r)
            self.symmetry_direction_menu.setValue(
                self.manager.grp.symmetry_direction.get()
            )
        self.build_control_list()

    def update_manager_orient_object_gui(self):
        self.std_orient_tf.textChangedCommand(lambda x: None)
        if self.manager and self.manager.orient_object:
            self.std_orient_tf.setText(self.manager.orient_object.name(long=False))
            self.std_orient_tf.setEditable(False)
            self.std_orient_button.setEnable(True)
        else:
            self.std_orient_tf.setText("")
            self.std_orient_tf.setEditable(True)
            self.std_orient_button.setEnable(False)
        self.std_orient_tf.textChangedCommand(
            pc.Callback(self.set_manager_orient_object)
        )

    def build_control_list(self):
        for child in self.controller_list_cl.getChildren():
            pc.deleteUI(child)
        if self.manager is None:
            return
        self.current_controls = []
        for c in self.manager.controls:
            control = StickyControl(ctrl=c)
            with pc.rowLayout(
                nc=6, cw6=self.cw6, adj=1, parent=self.controller_list_cl
            ) as row:
                pc.checkBox(label=control.name)
                with pc.popupMenu():
                    pc.menuItem(
                        "Select Control", c=pc.Callback(pc.select, control.ctrl)
                    )
                orient_obj = control.orient_object
                ootf = pc.textField(
                    text="" if not orient_obj else orient_obj.name(long=False),
                    pht="MMB Drop Object",
                    editable=not orient_obj,
                )
                with pc.popupMenu():
                    pc.menuItem(
                        "Clear",
                        c=pc.Callback(self.clear_control_orient_object, control, ootf),
                    )
                ootf.textChangedCommand(
                    (lambda x: None)
                    if orient_obj
                    else pc.Callback(self.set_control_orient_object, control, ootf)
                )
                sym_tf = pc.textField(pht="RMB Click", editable=False)
                with pc.popupMenu() as sym_menu:
                    pass
                self.update_sym_menu(control, sym_tf, sym_menu)

                pc.checkBoxGrp(
                    label="",
                    ncb=3,
                    cw4=self.trs_cws,
                    valueArray3=control.connection_array(),
                    of1=pc.Callback(control.disconnect, "t"),
                    on1=pc.Callback(control.connect, "t"),
                    of2=pc.Callback(control.disconnect, "r"),
                    on2=pc.Callback(control.connect, "r"),
                    of3=pc.Callback(control.disconnect, "s"),
                    on3=pc.Callback(control.connect, "s"),
                )
                pc.button(
                    label="Reweigh",
                    al="center",
                    w=self.reweight_w,
                    c=pc.Callback(self.reweight, control),
                )
                pc.iconTextButton(
                    i="delete.png",
                    w=self.del_w,
                    style="iconOnly",
                    c=pc.Callback(self.delete_control, control),
                )
            control.row = row
            self.current_controls.append(control)

    def update_sym_menu(self, control, sym_tf, sym_menu):
        sym_menu.deleteAllItems()

        sym_control = control.symmetry_control
        if not sym_control:
            sym_tf.setText("")
            pc.menuItem(
                parent=sym_menu,
                label="Create Mirrored Controller",
                c=pc.Callback(self.create_mirrored_controller, control),
            )
        else:
            sym_tf.setText(sym_control.name)

            pc.menuItem(
                parent=sym_menu,
                label=f"Push weights to {sym_control.name}",
                c=pc.Callback(self.push_weights_to_symmetry_controller, control),
            )
            pc.menuItem(
                parent=sym_menu,
                label=f"Break Connection to {sym_control.name}",
                c=pc.Callback(self.disconnect_mirrored_controller, control),
            )

    def batch_action(self, *args):
        action = self.controller_action_menu.getValue()
        # pre checks:
        if action == "Orient to Std. Object":
            if not self.manager.orient_object:
                pc.warning("There is no Std. Orient Object set. Set one first.")
                return
        checked_controls = []
        # check which controls are selected
        for c in self.current_controls:
            uis = c.row.getChildren()
            if uis[0].getValue():
                checked_controls.append(c)
        # perform action
        for c in checked_controls:
            if action == "Delete":
                self.delete_control(c)
            elif action == "Orient to Std. Object":
                self.set_control_orient_object(
                    c, c.row.getChildren()[1], self.manager.orient_object
                )
            elif action == "Clear Orient Object":
                c.set_orient_object(None)
                self.clear_control_orient_object(c, c.row.getChildren()[1])

    def select_all(self, state):
        for c in self.current_controls:
            c.row.getChildren()[0].setValue(state)

    def reset_gui(self):
        self.manager_option_menu.deleteAllItems()
        self.std_orient_tf.setText("")
        for child in self.controller_list_cl.getChildren():
            pc.deleteUI(child)
        self.enable_controllers_layouts(False)
        self.enable_manager_layouts(False)

    def select_controller_checkbox(self, controler):
        print(f"selecting controler checkbox for {controler}")

    def add_sticky_setup(self, *args):
        sel = pc.selected()
        if len(sel) != 1:
            pc.warning("Please select exactly one Mesh!")
            return
        result = pc.promptDialog(
            title=f"Create Setup for {sel[0].name()}",
            message="Enter Collection Name:",
            button=["OK", "Cancel"],
            defaultButton="OK",
            cancelButton="Cancel",
            dismissString="Cancel",
        )
        if result == "OK":
            name = pc.promptDialog(query=True, text=True)
            future_name = f"{name}_grp"
        else:
            return

        managers = get_sticky_managers(sel[0])
        if future_name in [m.name for m in managers]:
            pc.warning(
                f"Collection named '{name}' already exists. Please try again with another name."
            )
            return

        StickyControlManager().create(
            sel[0], name, callback=self.update_gui, callback_manager_list=managers
        )

    def add_controller(self, *args):
        sel = pc.selected()
        if not (
            sel
            and isinstance(sel[0], pc.general.MeshVertex)
            and sel[0].node() == get_visible_shape(self.manager.transform)
        ):
            pc.confirmDialog(
                title="Info",
                message=f"Please soft select Verts of {self.manager.transform}",
            )
            pc.select(self.manager.transform)
            pc.selectType(v=True)
            pc.selectMode(component=True)
            pc.softSelect(sse=True)
            return

        result = pc.promptDialog(
            title=f"Add Controller to {self.manager.name}",
            message="Controller Name:",
            button=["OK", "Cancel"],
            defaultButton="OK",
            cancelButton="Cancel",
            dismissString="Cancel",
        )
        if result == "OK":
            name = pc.promptDialog(query=True, text=True)
            StickyControl(name, self.manager, orient_to=self.manager.orient_object)
            self.update_gui(get_sticky_managers(self.manager.transform), self.manager)
            pc.selectMode(object=True)
        else:
            return

    def enable_manager_layouts(self, enable):
        self.manager_attributes_cl.setEnable(enable)
        self.controller_add_cl.setEnable(enable)
        self.controller_header_sl.setEnable(enable)

    def enable_controllers_layouts(self, enable):
        self.controller_header_sl.setEnable(enable)
        self.controller_list_cl.setEnable(enable)
        self.actions_rl.setEnable(enable)

    def manager_selected(self, manager_name):
        managers = get_sticky_managers(self.manager.transform)
        possible_managers = [m for m in managers if m.name == manager_name]
        if possible_managers:
            self.update_gui(managers, possible_managers[0])

    def set_manager_orient_object(self, *args):
        obj = pc.PyNode(self.std_orient_tf.getText())
        self.manager.set_orient_object(obj)
        self.update_manager_orient_object_gui()

    def clear_manager_orient_object(self, *args):
        self.manager.clear_orient_object()
        self.update_manager_orient_object_gui()

    def set_control_orient_object(self, control, tf, obj=None):
        obj = obj or pc.PyNode(tf.getText())
        control.set_orient_object(obj)
        tf.textChangedCommand(lambda x: None)
        tf.setText(obj.name(long=False))
        tf.setEditable(False)

    def clear_control_orient_object(self, control, tf):
        control.set_orient_object(None)
        tf.textChangedCommand(lambda x: None)
        tf.setText("")
        tf.textChangedCommand(pc.Callback(self.set_control_orient_object, control, tf))
        tf.setEditable(True)

    def set_search_string(self, text):
        st = legalize_text(text)
        self.search_tfg.setText(st)
        self.manager.grp.search.set(st)

    def set_replace_string(self, text):
        st = legalize_text(text)
        self.replace_tfg.setText(st)
        self.manager.grp.attr("replace").set(st)

    def create_mirrored_controller(self, control):
        s = self.manager.grp.attr("search").get()
        r = self.manager.grp.attr("replace").get()
        name = new_name = control.name
        if s:
            new_name = name.replace(s, r)
        if new_name == name:
            new_name = f"{name}_sym"
        control.create_symmetry_control(
            new_name, sym_matrix=control.manager.symmetry_matrix
        )
        self.build_control_list()

    def disconnect_mirrored_controller(self, control):
        control.remove_symmetry_control()
        self.build_control_list()

    def push_weights_to_symmetry_controller(self, control):
        control.push_weights_to_symmetry_controller()

    def set_symmetry_direction(self, item):
        self.manager.grp.symmetry_direction.set(item)

    def reweight(self, control: StickyControl):
        sel = pc.selected()
        if not (
            sel
            and isinstance(sel[0], pc.general.MeshVertex)
            and sel[0].node() == self.manager.transform.getShape()
        ):
            pc.confirmDialog(
                title="Info",
                message=f"Please soft select Verts of {self.manager.transform}",
            )
            pc.select(self.manager.transform)
            pc.selectType(v=True)
            pc.selectMode(component=True)
            pc.softSelect(sse=True)
            return
        control.edit_weights()
        pc.selectMode(object=True)

    def delete_control(self, control):
        control.delete()
        pc.deleteUI(control.row)
        self.current_controls.remove(control)

    def kill_script_jobs(self, *args):
        for job in self.script_jobs:
            pc.scriptJob(kill=job, force=True)
