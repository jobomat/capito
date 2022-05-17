"""Module to handle "tags" with maya-nodes. A tag is only a normal string attribute."""
from collections import defaultdict
from typing import List, Dict

import pymel.core as pc


def tag_node(node:pc.nodetypes.DependNode, tag_key: str, tag_value: str=""):
    """Attach attribute named 'tag_key' with 'tag_value' to PyMel node 'node'."""
    if not node.hasAttr(tag_key):
        node.addAttr(tag_key, dt="string")
    node.attr(tag_key).set(tag_value)


def get_tagged_nodes(tag_key: str, tag_value: str, **kwargs) -> List[pc.nodetypes.DependNode]:
    nodes = pc.ls(**kwargs)
    tagged_nodes = []
    for node in nodes:
        if node.hasAttr(tag_key):
            if node.asset("tag_key").get() == tag_value:
                tagged_nodes.append(node)
    return tagged_nodes


def get_tagged_dag_nodes(tag_key: str, tag_value: str) -> List[pc.nodetypes.DependNode]:
    return get_tagged_nodes(tag_key, tag_value, dag=True)


def get_tag_dict(tag_key: str, **ls_kwargs) -> Dict[str, List[pc.nodetypes.DependNode]]:
    """Nodes with tag 'tag_key' are filtered.
    Then a dict of following form is returned:
    {
        tag_value_1: [node1, node2, ...],
        tag_value_2: [node1, node2, ...],
        ...
    }
    """
    node_dict = defaultdict(list)
    for node in pc.ls(**ls_kwargs):
        if node.hasAttr(tag_key):
            node_dict[node.attr(tag_key).get()].append(node)
    return node_dict
