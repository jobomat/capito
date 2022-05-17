from typing import Tuple

import maya.OpenMaya as om
import pymel.core as pc


def place_at_point(
    child: pc.nodetypes.Transform, parent: pc.nodetypes.Transform, orient: bool = False
) -> None:
    """Places or places and orients child at parent.

    :param child: The transform node to be placed.
    :type child: :class:`pymel.core.nodetypes.Transform`
    :param parent: The transform node to place child at.
    :type locator: :class:`pymel.core.nodetypes.Transform`
    :param orient: If True additionally orients the child to parent.
    :type orient: bool

    :returns: None
    :rtype: None
    :raises: None
    """
    if orient:
        pc.delete(pc.parentConstraint(parent, child))
    else:
        pc.delete(pc.pointConstraint(parent, child))


def locator_at_point(
    point: pc.nodetypes.Transform,
    locator: bool = True,
    orient: bool = False,
    name: str = None,
) -> pc.nodetypes.Transform:
    """Returns a locator or empty transform at 'point'.

    :param point: The transform node to create the locator at.
    :type point: :class:`pymel.core.nodetypes.Transform`
    :param locator: If True creates a locator else an empty transform.
    :type locator: bool
    :param orient: If True additionally orients the locator to point.
    :type orient: bool
    :name: The name prefix for the locator to be created.
    :type name: str

    :returns: A locator or empty transform.
    :rtype: :class:`pymel.core.nodetypes.Transform`
    :raises: TypeError
    """
    if not isinstance(point, pc.nodetypes.Transform):
        raise TypeError('Parameter "point" must be of type pymel-Transform.')

    name = "{}_loc".format(name or point.name())
    if locator:
        loc = pc.spaceLocator(name=name)
    else:
        loc = pc.group(empty=True, name=name)
    place_at_point(loc, point, orient)

    return loc


def distance_between(t1: pc.nodetypes.Transform, t2: pc.nodetypes.Transform) -> float:
    """Returns the exact distance between transforms t1 and t2.
    Not calculated using python (sqrt((x2-x1)**2 ...) because
    of loss of precision!

    :param t1: Transform that is the starting point of measurement.
    :type t1: :class:`pymel.core.nodetypes.Transform`
    :param t2: Transform that is the end point of measurement.
    :type t2: :class:`pymel.core.nodetypes.Transform`

    :returns: The world distance between t1 and t2
    :rtype: float
    :raises: None
    """
    distance_node = pc.createNode("distanceBetween")
    loc1 = pc.group(empty=True)
    loc2 = pc.group(empty=True)
    pc_temp = [pc.pointConstraint(t1, loc1), pc.pointConstraint(t2, loc2)]
    pc.delete(pc_temp)
    loc1.translate >> distance_node.point1
    loc2.translate >> distance_node.point2
    dist = distance_node.getAttr("distance")
    pc.delete(loc1, loc2, distance_node)
    return dist


def hierarchy_len(
    parent: pc.nodetypes.Transform, child: pc.nodetypes.Transform
) -> float:
    """Returns the sum of distances between pivots of a hierarchical
    structure starting with parent and ending with child. Useful e.g.
    to get the combined (bone) length of a joint-chain.

    :param parent: Starting point of the hierarchy
    :type parent: :class:`pymel.core.nodetypes.Transform`
    :param child: End point of the hierarchy
    :type child: :class:`pymel.core.nodetypes.Transform`

    :returns: Combined length from parent over child1, 2, ... to child
    :rtype: float
    :raises: None
    """
    chain = [child] + child.getAllParents()
    dist = []
    while chain[0] != parent and len(chain):
        child = chain.pop(0)
        dist.append(distance_between(child, chain[0]))
    return sum(dist)


def get_free_md_channels(
    node: pc.nodetypes.MultiplyDivide = None,
    name: str = None
) -> Tuple[pc.general.Attribute]:
    """Returns the first free channel of a given multiplyDivide node.
    If no node is given or no channel is availible creates a new node.

    :param node: The multiplyDivide node
    :type node: :class:`pymel.core.nodetypes.multiplyDivide`
    :param name: Name of the node to create.
    :type name: str

    :returns: Tuple with the free to connect in- and output channel
    :rtype: :class:`pymel.core.nodetypes.Attribute`
    :raises: None
    """
    input_1_channels = ["input1X", "input1Y", "input1Z"]
    input_2_channels = ["input2X", "input2Y", "input2Z"]
    output_channels = ["outputX", "outputY", "outputZ"]

    if not node:
        node = pc.createNode("multiplyDivide", name=name or "multDiv")
        return (
            node.attr(input_1_channels[0]),
            node.attr(input_2_channels[0]),
            node.attr(output_channels[0]),
        )

    for i, channel in enumerate(input_1_channels):
        if not node.attr(channel).isConnected():
            return (
                node.attr(input_1_channels[i]),
                node.attr(input_2_channels[i]),
                node.attr(output_channels[i]),
            )


def insert_normalized_scale_node(
    unnormalized_attr, scalefactor_attr, normalize_node=None, name=None
):
    """Adds a multyplyDivide node to unnormalized_attr (which is usually
    the output of another multyplyDivide node) and compensates its output
    by a division with scalefactor_attr. Reconnects normalized value to old destination.

    :param unnormalized_attr: The output attribute to be normalized.
    :type unnormalized_attr: :class:`pymel.core.nodetypes.Attribute`
    :param scalefactor_attr: The attribute by which to normalize.
    :type scalefactor_attr: :class:`pymel.core.nodetypes.Attribute`
    :param normalize_node: If given it is tried to use a free channel of it.
    :type normalize_node: :class:`pymel.core.nodetypes.multiplyDivide`
    :param name: The name of newly created nodes.
    :type name: str

    :returns: The multiplyDivide node that was used
    :rtype: :class:`pymel.core.nodetypes.multiplyDivide`
    :raises: None
    """
    unnormalized_attr_node = unnormalized_attr.node()
    name = name or unnormalized_attr_node.name()[:-4]

    dest_attrs = unnormalized_attr.listConnections(plugs=True)

    normalize_node_channels = get_free_md_channels(
        node=normalize_node, name=f"{name}_normalize_div"
    )

    normalize_node = normalize_node_channels[0].node()
    normalize_node.setAttr("operation", 2)

    unnormalized_attr >> normalize_node_channels[0]
    scalefactor_attr >> normalize_node_channels[1]
    for dest_attr in dest_attrs:
        normalize_node_channels[2] >> dest_attr

    return normalize_node


def scalefactor_node(m1, m2, div_node=None, initial_len=None, name=None):
    """Set up nodes to calculate scale factor.
    (distance(m1 to m2) / initial_len)
    If initial_len is not provided the current distance(m1 to m2) will be used
    If div_node is specified the next free channel of this node will be used.
    Otherwise a new MulitiplyDivide node will be created.

    :param m1: Measurement point 1
    :type m1: :class:`pymel.core.nodetypes.Transform`
    :param m2: Measurement point 2
    :type m2: :class:`pymel.core.nodetypes.Transform`
    :param div_node: Divide-Node to use
    :type div_node: `pymel.core.nodetypes.MultiplyDivide`
    :param initial_len: The denominator of the scale-calculation.
    :type initial_len: float
    :param name: Name prefix for all created nodes.
    :type name: str

    :returns: Tuple with multyplyDivide node
        and the attribute where the result will be present.
    :rtype: (
        `pymel.core.nodetypes.MultiplyDivide`,
        `pymel.core.general.Attribute`
    )
    :raises: None
    """

    name = name or "{}_to_{}".format(m1.name(), m2.name())

    div_node_channels = get_free_md_channels(
        node=div_node, name="{}_normalize_div".format(name)
    )
    div_node = div_node_channels[0].node()
    div_node.setAttr("operation", 2)

    distance_node = pc.createNode("distanceBetween", name="{}_dist".format(name))

    m1.getShape().worldMatrix >> distance_node.inMatrix1
    m2.getShape().worldMatrix >> distance_node.inMatrix2
    distance_node.distance >> div_node_channels[0]

    initial_len = initial_len or distance_node.getAttr("distance")
    div_node_channels[1].set(initial_len)

    return div_node, div_node_channels[2]


def point_on_curve_info_nodes(
    curve: pc.nodetypes.NurbsCurve, num_points: int, name: str = None
) -> list:
    name = name or curve.name()
    u_step = 1.0 / (num_points - 1)
    u_values = [x * u_step for x in range(num_points)]
    info_nodes = []
    for i, u_value in enumerate(u_values):
        info_node = pc.createNode("pointOnCurveInfo")
        info_node.turnOnPercentage.set(1)
        info_node.parameter.set(u_value)
        info_node.rename(f"{name}_poc")
        curve.attr("worldSpace[0]") >> info_node.inputCurve
        info_nodes.append(info_node)
    return info_nodes


def distance_points_between_to_curves(
    curve1: pc.nodetypes.NurbsCurve,
    curve2: pc.nodetypes.NurbsCurve,
    num_points: int,
    name: str = None,
) -> list:
    name = name or f"{curve1.name()}_{curve2.name()}"
    info_nodes_1 = point_on_curve_info_nodes(
        curve1, num_points, f"{curve1.name()}_info"
    )
    info_nodes_2 = point_on_curve_info_nodes(
        curve2, num_points, f"{curve2.name()}_info"
    )
    dist_nodes = []
    i = 1
    for info_1, info_2 in zip(info_nodes_1, info_nodes_2):
        dist_node = pc.createNode("distanceBetween")
        dist_node.rename(f"{name}_{i}_dist")
        info_1.position >> dist_node.point1
        info_2.position >> dist_node.point2
        dist_nodes.append(dist_node)
        i += 1
    return dist_nodes


def create_pairblend(
    in_obj_1: pc.nodetypes.Transform,
    in_obj_2: pc.nodetypes.Transform,
    result_obj: pc.nodetypes.Transform,
    name: str = None,
    channels=["translate", "rotate"],
):
    """creates ab pairblend from in_obj_1.channel and in_obj2.channel to result_obj.channel"""
    pairblend = pc.createNode(
        "pairBlend",
        name=f"{in_obj_1.name()}_{in_obj_2.name()}_blend" if name is None else name,
    )
    for attr in channels:
        in_obj_1.attr(attr.lower()) >> pairblend.attr(f"in{attr.capitalize()}1")
        in_obj_2.attr(attr.lower()) >> pairblend.attr(f"in{attr.capitalize()}2")
        pairblend.attr(f"out{attr.capitalize()}") >> result_obj.attr(attr.lower())
    return pairblend


def attach_group_to_edge(edge, name="test", grp_count=1, ctrl=True):
    pnt_on_crv_grps = []
    shape = edge.node()
    edge_num = edge.index()
    curve_from_edge = pc.createNode(
        "curveFromMeshEdge", name="{}_crv_from_edge{}".format(name, edge_num)
    )
    shape.worldMesh.worldMesh[0] >> curve_from_edge.inputMesh

    u_step = 1 if grp_count == 1 else 1.0 / float(grp_count - 1)

    for i in range(grp_count):
        point_on_curve_info = pc.createNode(
            "pointOnCurveInfo", name="{}_pnt_on_crv{}_{}".format(name, edge_num, i)
        )
        point_on_curve_info.setAttr("turnOnPercentage", 1)
        pnt_on_crv_grp = pc.group(
            empty=True,
            name="{}_e{}_u{}_grp".format(name, edge_num, int(i * u_step * 100)),
        )
        pnt_on_crv_grp.addAttr("uPos", k=True)
        pnt_on_crv_grp.uPos >> point_on_curve_info.parameter
        pnt_on_crv_grp.setAttr("uPos", i * u_step)

        if ctrl:
            offset_grp = pc.group(empty=True, name="{}_offset_grp".format(name))
            ctrl = pc.circle(n="{}_ctrl".format(name), radius=0.2)[0]
            pc.delete(ctrl, ch=True)
            pc.parent(ctrl, offset_grp)
            pc.parent(offset_grp, pnt_on_crv_grp)

        curve_from_edge.setAttr("edgeIndex[0]", edge_num)
        curve_from_edge.outputCurve >> point_on_curve_info.inputCurve
        point_on_curve_info.position >> pnt_on_crv_grp.translate

        pnt_on_crv_grps.append(pnt_on_crv_grp)

    return pnt_on_crv_grps
