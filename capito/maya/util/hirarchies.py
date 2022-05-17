# encoding: utf-8
import pymel.core as pc
from capito.maya.util.names import name_with_numbered_postfix


def list_all_parents(transform):
    parents = []
    while True:
        parent = transform.getParent()
        if parent:
            parents.append(parent)
            transform = parent
        else:
            return parents


def connect_hirarchy(driver, driven, connect_function=None, condition_function=None):
    """Connects two (identical) hirarchical structures via a connection function
    if the optionally provided condition function returns True.

    :param driver: Top Node of the first hirarchy
    :type driver: :class:`pymel.core.nodetypes.Transform`
    :param driven: Top Node of the second hirarchy.
    :type driven: :class:`pymel.core.nodetypes.Transform`
    :param connect_function: The function to execute with params driver/child, driven/child
    :type connect_function: function
    :param condition_function: The function to specify a condition for the connection to happen
    :type condition_function: function

    :returns: None
    :rtype: None
    :raises: None

    Example that executes an orientConstraint-command for all children of driver and driven
    if the driver_node is of type "joint" and its name does not end with "_end":

    j1, j2 = pc.selected()  # Two top joints of identical joint-hirarchies are selected.
    connect_hirarchy(
        j1, j2, pc.orientConstraint,
        lambda x, y: not x.name().endswith("_end") and x.type() == "joint"
    )
    """
    if condition_function is None or condition_function(driver, driven):
        connect_function(driver, driven)
    for m, s in zip(driver.getChildren(), driven.getChildren()):
        connect_hirarchy(m, s, connect_function, condition_function)


def add_group(transform: pc.nodetypes.Transform, name: str = None):
    if name is None:
        name = transform.name()
    name = name_with_numbered_postfix(name, "_grp")
    transform_parent = transform.getParent()
    grp = pc.group(empty=True, name=name)
    cnstr = pc.parentConstraint(transform, grp)
    pc.delete(cnstr)
    if transform_parent:
        pc.parent(grp, transform_parent)
    pc.parent(transform, grp)
    return grp
