from typing import Any, List
import maya.OpenMaya as om1
import maya.api.OpenMaya as om
import pymel.core as pc

from capito.maya.geo.shapes import get_used_shapes


def list_inputs_of_type(transform:pc.nodetypes.Transform, nodetype: Any):
    """List all nodes of specific type found in history of selected transfroms shapes.

    :param transform: The transform which inputs (history) will be examined.
    :type transform: pymel.nodetypes.Transform
    :param nodetype: The nodetype to list
    :type nodetype: pymel.nodetypes.*
    :return: A list of matching nodes
    :rtype: list
    """
    return [s for s in transform.listHistory() if isinstance(s, nodetype)]


def get_orig_shape(transform: pc.nodetypes.Transform):
    """Tries to return the original shape of a transform.
    The original shape is the undeformed input into the deformer chain.
    If no 'shapeOrig' is found returns None.

    :param transform: The pymel transform node to check.
    :type transform: :class:`pymel.core.nodetypes.Transform`
    :return: The original shape node or None
    :rtype: :class:`pymel.core.nodetypes.Mesh`
    :raises: None
    """
    all_shapes = transform.getShapes()
    if len(all_shapes) == 1:
        return all_shapes[0]
    original_shapes = [s for s in transform.getShapes() if s.intermediateObject.get()]
    if original_shapes:
        return original_shapes[0]
    return None


def get_visible_shape(transform: pc.nodetypes.Transform):
    all_shapes = transform.getShapes()
    if len(all_shapes) == 1:
        return all_shapes[0]
    visible_shapes = [s for s in all_shapes if not s.intermediateObject.get()]
    if visible_shapes:
        return visible_shapes[0]
    return None


def duplicate_orig_shape(transform: pc.nodetypes.Transform):
    """Duplicates the orig shape of given transform in its base position

    :param transform: The transform whichs orig shape will be duplicated.
    :type transform: pc.nodetypes.Transform
    :return: The duplicated transform in its base position.
    :rtype: pc.nodetypes.Transform
    """
    shape = get_orig_shape(transform)

    mesh_node = pc.createNode("mesh")
    shape.outMesh >> mesh_node.inMesh

    dup = pc.duplicate(mesh_node.getParent())
    pc.delete(mesh_node.getParent())

    pc.select(dup[0])
    pc.mel.eval("sets - e - forceElement initialShadingGroup")
    return dup[0]


def get_soft_selection_values():
    """Returns a dict based on current soft vertex selection.
    Dict-Key is representing the vertex-index and is of type int.
    Dict-Value is representing the selection weight and is of type float.

    :rtype: dict{vertindex (int): weight (float)}
    :raises: None
    """
    rich_selection = om.MGlobal.getRichSelection()

    sel_iter = om.MItSelectionList(
        rich_selection.getSelection(), om.MFn.kMeshVertComponent
    )
    weight_dict = {}

    while not sel_iter.isDone():
        _, verts = sel_iter.getComponent()
        fn_comp = om.MFnSingleIndexedComponent(verts)

        for i in range(fn_comp.elementCount):
            weight_dict[fn_comp.element(i)] = fn_comp.weight(i).influence
        sel_iter.next()

    return weight_dict


def set_cluster_pivots_to_pos(cluster_handle: pc.nodetypes.Transform, pos: List[float, float, float]):
    """Sets visual appearance, scale- and rotate pivot of cluster to pos

    :param cluster_handle: The pymel transform of the cluster.
    :type cluster_handle: :class:`pymel.core.nodetypes.Transform`
    :param pos: The world x,y,z for the cluster pivot.
    :type pos: list or tuple of three floats

    :returns: None
    :rtype: None
    :raises: None
    """
    cluster_handle.setAttr("scalePivot", pos)
    cluster_handle.setAttr("rotatePivot", pos)
    cluster_handle.getShape().setAttr("origin", pos)


def create_soft_cluster(name=None, shape=None, weight_dict=None, pivot_pos=None):
    """Creates a cluster deformer with it's influence weights based on weight_dict.
    If no weight_dict is provided the currently active soft selection will be used.
    If no shape is given the cluster will be created for the object the active soft
    selection belongs to.
    Info: All vertices of 'shape' will be added to the weightlist of the cluster.

    :param name: Name prefix for the created nodes.
    :type name: str
    :param shape: A mesh node on which the cluster will be acting.
    :type shape: :class:`pymel.core.nodetypes.Mesh`
    :param weight_dict: A list of Tuples (vertex-index, weight).
    :type weight_dict: list((int, float))
    :param pivot_pos: The world x,y,z for the cluster pivot.
    :type pivot_pos: list of three floats

    :returns: The created ClusterHandle
    :rtype: pymel.nodetypes.Transform
    :raises: None
    """
    weight_dict = weight_dict or get_soft_selection_values()

    if shape is None:
        shape = pc.selected(fl=True)[0].node()
    # if not specified the max value in the dict will be used
    if pivot_pos is None:
        highest_weight_index = max(weight_dict, key=lambda key: weight_dict[key])
        pivot_pos = shape.vtx[highest_weight_index].getPosition(space="world")

    name = name or f"{shape.name()}_{len(shape.listHistory(type='cluster')) + 1}"

    pc.select(shape.getParent(), r=True)
    cluster, cluster_handle = pc.cluster(relative=True, name=f"{name}_cl")
    # initialize whole shape with one.
    # Otherwise editing via edit_soft_cluster_weights will not be possible
    pc.percent(cluster, shape, v=1)

    set_cluster_pivots_to_pos(cluster_handle, pivot_pos)

    edit_soft_cluster_weights(cluster_handle, weight_dict)

    return cluster_handle


def edit_soft_cluster_weights(cluster_handle, weight_dict=None):
    """Edit the weights of an existing cluster based on a weight_dict created by
    function 'get_soft_selection_values()'.
    """
    weight_dict = weight_dict or get_soft_selection_values()

    cluster = cluster_handle.attr("worldMatrix").listConnections(type="cluster")[0]

    weight_plug = om1.MPlug()
    sel = om1.MSelectionList()
    sel.add(f"{cluster.name()}.weightList[0].weights")
    sel.getPlug(0, weight_plug)

    ids = om1.MIntArray()
    weight_plug.getExistingArrayAttributeIndices(ids)
    count = ids.length()

    for i in range(count):
        weight_plug.elementByLogicalIndex(ids[i]).setFloat(weight_dict.get(i, 0.0))
