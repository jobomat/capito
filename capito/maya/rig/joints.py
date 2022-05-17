from typing import List

import pymel.core as pc

from capito.maya.util.hirarchies import add_group
from capito.maya.geo.transforms import place_along_curve


def get_twist_axis(jnt):
    axes = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    child_translation = jnt.getChildren()[0].translate.get()
    val = 0
    index = None
    for i, t in enumerate(child_translation):
        if t > val:
            val = t
            index = i * 2
        elif abs(t) > val:
            val = abs(t)
            index = i * 2 + 1
    return axes[index]


def joint_chain_replicator(
    joint_chain: list, name: str, search: str, replicas=["_ik", "_fk"]
):
    """
    Replicates the given hirarchicaly related joints for each name in 'replicas'.
    Replaces the 'search' string with the replica string.
    """
    rep_parents = []
    parent = None
    for rep in replicas:
        for i, joint in enumerate(joint_chain):
            n = joint.name().replace(search, "")
            dup = pc.duplicate(joint, name=f"{n}{rep}")[0]
            for child in dup.getChildren():
                pc.delete(child)
            if i == 0:
                grp = pc.group(dup, name=f"{name}{rep}_grp")
                pc.parent(grp, world=True)
                rep_parents.append(grp)
            else:
                pc.parent(dup, parent)
            parent = dup
    return rep_parents


def single_joint_ctrl(name: str, postfix: str = "_bnd") -> pc.nodetypes.Joint:
    """Creates a single joint as children of a NurbsCircle and two groups."""
    jnt = pc.joint(name=f"{name}{postfix}", p=(0, 0, 0))
    jnt.visibility.set(False)
    ctrl = pc.circle(ch=False, normal=(1, 0, 0), name=f"{name}_ctrl")[0]
    ctrl_null = add_group(add_group(ctrl, f"{name}_offset"), f"{name}_null")
    pc.parent(jnt, ctrl)
    return jnt


def create_joint_controls_along_curve(
    curve: pc.nodetypes.NurbsCurve,
    up_object: pc.nodetypes.Transform,
    num_controls: int,
    name: str = None,
) -> List[pc.nodetypes.Joint]:
    """
    Creates 'num_controls' controls placed evenly spaced at and oriented along 'curve'.
    The control contains a single joint and is wrapped in two offset groups.
    """
    name = name or "_".join(curve.name().split("_")[:-1])
    jnt_list = [single_joint_ctrl(f"{name}_{i+1}") for i in range(num_controls)]
    null_list = [j.getParent().getParent().getParent() for j in jnt_list]
    # Place the joints equidistributed along the curve:
    place_along_curve(null_list, curve, up_object=up_object)
    return jnt_list


def split(joint, num_segments=2):
    child_joints = joint.getChildren(f=True, c=True, type="joint")

    if not child_joints:
        pc.warning("Joint has no child-joint. Split cannot be performed.")
        return
    if len(child_joints) > 1:
        pc.warning("Joint has more than one child-joint. Aborted.")
        return

    radius = joint.getAttr("radius")
    name = joint.name()

    child_joint = child_joints[0]
    distances = child_joint.getTranslation()
    deltas = [dist / num_segments for dist in distances]

    for i in range(1, num_segments):
        new_joint = pc.insertJoint(joint)
        new_joint = pc.joint(
            new_joint,
            edit=True,
            co=True,
            r=True,
            p=deltas,
            rad=radius,
            name="{}_seg_{}".format(name, i),
        )
        joint = new_joint


class SplitSelected:
    def __init__(self):
        self.win = "splitSelectedJoint_win"

        if pc.window(self.win, exists=True):
            pc.deleteUI(self.win)

        self.ui()

    def ui(self):
        with pc.window(
            self.win, title="Split Selected Joints", widthHeight=[300, 50], toolbox=True
        ):
            pc.columnLayout(adjustableColumn=True)
            self.num_seg_intfield = pc.intSliderGrp(
                label="Number of Segments",
                columnWidth3=[110, 25, 165],
                field=True,
                minValue=2,
                maxValue=20,
                fieldMinValue=2,
                fieldMaxValue=50,
                value=4,
            )
            with pc.rowLayout(nc=2):
                pc.button(label="Split", w=145, c=pc.Callback(self.split))
                pc.button(label="Cancel", w=145, c=pc.Callback(pc.deleteUI, self.win))

    def split(self, arg=None):
        sel = pc.selected(type="joint")
        num_segments = pc.intSliderGrp(self.num_seg_intfield, q=True, value=True)

        for joint in sel:
            split(joint, num_segments)


def create_ribs_from_copies(orig, copies):
    """Creates 'rib-like' extensions of joints.
    :param orig: The top joint of the hirarchy to attach the ribs
    :type orig:  :class:`pymel.core.nodetypes.Joint`
    :param copies: The copied and translated top joint (+children)
    :type copies:  list of :class:`pymel.core.nodetypes.Joint`

    Example usage:
    sel = pc.selected()
    orig, copies = sel[0], sel[1:]
    """
    parents = orig.getChildren(ad=True)
    parents.append(orig)

    ribs_list = []
    for rib in copies:
        children = rib.getChildren(ad=True)
        children.append(rib)
        ribs_list.append(children)

    ribs_list = zip(*ribs_list)

    for p, ribs in zip(parents, ribs_list):
        for i, c in enumerate(ribs, 1):
            c.rename("{}_rib_{}".format(p.name(), i))
            pc.parent(c, p)
