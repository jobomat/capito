import pymel.core as pc
from capito.maya.rig.joints import joint_chain_replicator
from capito.maya.rig.utils import create_pairblend
from capito.maya.rig.icons import import_blendshaped_ik_fk
from capito.maya.geo.shapes import add_shapes

# 1. set correct name, select upper, lower, wrist:
name = "l_arm"

joint_chain = pc.selected()

replica_groups = joint_chain_replicator(
    joint_chain, name, "_bnd", ["_ik", "_fk", "_result"]
)

chains = []
for grp in replica_groups:
    chains.append(grp.getChildren(ad=True))

pair_blends = []
for in1, in2, res in zip(*chains):
    pair_blends.append(create_pairblend(in1, in2, res))

for fk_jnt in replica_groups[1].getChildren(ad=True):
    ctrl = pc.circle()[0]
    add_shapes(ctrl, fk_jnt)
    pc.delete(ctrl)

ik_fk_controler = import_blendshaped_ik_fk(name)
pc.parent(ik_fk_controler.getParent(), joint_chain[-1])
ik_fk_controler.getParent().setTranslation((0, 1, 0))

if not ik_fk_controler.hasAttr("ik_fk"):
    ik_fk_controler.addAttr("ik_fk", at="byte", minValue=0, maxValue=1, k=True)

for pair_blend in pair_blends:
    ik_fk_controler.attr("ik_fk") >> pair_blend.weight

if not ik_fk_controler.hasAttr("fk_vis"):
    ik_fk_controler.addAttr("fk_vis", at="byte", minValue=0, maxValue=1)
if not ik_fk_controler.hasAttr("ik_vis"):
    ik_fk_controler.addAttr("ik_vis", at="byte", minValue=0, maxValue=1)
set_range = pc.createNode("setRange", name=f"{name}_ikfkvis_setRange")
set_range.minX.set(1)
set_range.maxX.set(0)
set_range.oldMinX.set(0.999)
set_range.oldMaxX.set(1)
set_range.minY.set(0)
set_range.maxY.set(1)
set_range.oldMinY.set(0)
set_range.oldMaxY.set(0.001)
ik_fk_controler.attr("ik_fk") >> set_range.valueX
ik_fk_controler.attr("ik_fk") >> set_range.valueY
set_range.outValueX >> ik_fk_controler.attr("ik_vis")
set_range.outValueY >> ik_fk_controler.attr("fk_vis")

ik_fk_controler.fk_vis >> replica_groups[1].getChildren()[0].visibility

for res, orig in zip(reversed(replica_groups[2].getChildren(ad=True)), joint_chain):
    pc.parentConstraint(res, orig)

pc.group(*replica_groups, name=f"{name}_modules_grp")

# create your ik-setup
# --> on ik-chain set the prefered angle
# --> create Rotate-Plane-IK, Pole-Vector
# --> orient ik-chain-wrist to wrist-controller
# --> connect ik_fk_icon.ik_vis to all ik-controllers (wrist, pole)

# finalize:
# --> create a buffer joint (copy of upper_arm, delete its children)
# --> parent original upper to buffer
# --> create single chain ik from clavicle to buffer
# --> create a control for this ik-handle
# --> point constrain the module_grp to the buffer joint
