import pymel.core as pc
from pymel.core.general import MayaAttributeError

def connect_object_attributes(from_objs, from_attrs, to_objs, to_attrs):
    """
    lame
    """
    for f, t in zip(from_objs, to_objs):
        for from_attr, to_attr in zip(from_attrs, to_attrs):
            f.attr(from_attr) >> t.attr(to_attr)


def add_string_attr(pymel_node: pc.nodetypes.DependNode, attr_name: str):
    """Add a string attribute to a PyMel node."""
    if pymel_node.hasAttr(attr_name):
        return
    pymel_node.addAttr(attr_name, dt="string")
    

def set_string_attr(pymel_node: pc.nodetypes.DependNode, attr_name: str, value: str):
    """Set a string attribute of a PyMel node. 
    If the attribute does not exist it will be created.
    """
    add_string_attr(pymel_node, attr_name)
    pymel_node.attr(attr_name).set(value)


def silent_delete_attr(pymel_node: pc.nodetypes.DependNode, attr_name: str):
    """Delete an attribute of a PyMel node."""
    if not pymel_node.hasAttr(attr_name):
        print(f"{pymel_node}.{attr_name} cannot be deleted (attribute doesn't exist).")
        return
    try:
        pymel_node.deleteAttr(attr_name)
    except MayaAttributeError:
        print(f"{pymel_node}.{attr_name} cannot be deleted (not unique).")
    except RuntimeError:
        print(f"{pymel_node}.{attr_name} cannot be deleted (locked or static).")