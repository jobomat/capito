import json
from random import uniform
from typing import List

import pymel.core as pc

from capito.maya.viewport.wireframe import colorize


class Branch:
    def __init__(self, branch_manager, node=None, curve=None, name=None, density=5, attach_threshold=0.6):
        self.branch_manager = branch_manager
        if not node:
            self._create_main_node()
            self.curve = curve
            self._create_function_nodes()
            self.density = density
            self.attach_threshold = attach_threshold
            self.rename_nodes(name or self.curve.name())
        else:
            self.node = node
    
    def nearest_u_and_point_to(self, pos):
        npoc = self.node.nearestPointOnCurve.listConnections()[0]
        npoc.inPosition.set(pos)
        return npoc.parameter.get(), npoc.position.get()
        
    def check_relationship(self, branch: "Branch"):
        if self == branch:
            return False
        start_pos = self.start_pos
        u_value, pos = branch.nearest_u_and_point_to(start_pos)
        # if self is child of branch
        if start_pos.distanceTo(pos) < self.attach_threshold:
            self.set_parent(branch)
            self.parent_u_pos = u_value
            self.curve.getShape().cv[0].setPosition(
                branch.get_pos_at_u(u_value)
            )
            self.curve.getShape().updateCurve()

    def set_parent(self, parent):
        parent.node.child_branches >> self.node.parent_branch
        
    def get_max_parameter(self):
        return float(
            len(self.curve.getShape().cv) - self.curve.getShape().degree()
        )
        
    def rename_nodes(self, name):
        self.node.rename(f"{name}_branchNode")
        self.node.curveInfo.listConnections()[0].rename(f"{name}_lenInfo")
        self.node.pointOnCurveInfo.listConnections()[0].rename(f"{name}_posInfo")
        self.node.nearestPointOnCurve.listConnections()[0].rename(f"{name}_nearestPoint")
        self.node.remapValue.listConnections()[0].rename(f"{name}_scaleMap")

    def get_positions(self):
        num_positions = int(self.length * self.density)
        step = self.get_max_parameter() / num_positions
        return [self.get_pos_at_u(i * step) for i in range(num_positions)]
        
    def recurse_positions(self):
        pos = self.get_positions()
        for branch in self.get_child_branches():
            pos.extend(branch.recurse_positions())
        return pos

    def get_pos_at_u(self, u):
        self.u = u
        return list(self.pos)

    def get_child_branches(self):
        connections = self.node.child_branches.listConnections()
        return [self.branch_manager._branch_map[c] for c in connections]
            
    def _create_main_node(self):
        self.node = pc.createNode("network")
        self.node.addAttr("branch_manager_node", at="message") 
        self.node.addAttr("density", at="float")
        self.node.addAttr("attach_threshold", at="float")
        self.node.addAttr("curve", at="message")
        self.node.addAttr("curveInfo", at="message")
        self.node.addAttr("pointOnCurveInfo", at="message")
        self.node.addAttr("nearestPointOnCurve", at="message")
        self.node.addAttr("remapValue", at="message")
        self.node.addAttr("child_branches", at="message")
        self.node.addAttr("parent_branch", at="message")
        self.node.addAttr("parent_u_pos", at="float")
        self.node.addAttr("u_value", at="float")
        
    def _create_function_nodes(self):
        # curveInfo for length
        node = pc.createNode("curveInfo")
        self.curve.getShape().attr("worldSpace[0]") >> node.inputCurve
        node.addAttr("branch_node", at="message")
        self.node.curveInfo >> node.branch_node
        # pointOnCurveInfoNode for positions
        node = pc.createNode("pointOnCurveInfo")
        # node.turnOnPercentage.set(True)
        self.curve.getShape().attr("worldSpace[0]") >> node.inputCurve
        self.node.u_value >> node.parameter
        node.addAttr("branch_node", at="message")
        self.node.pointOnCurveInfo >> node.branch_node
        # nearestPointOnCurve for distances
        node = pc.createNode("nearestPointOnCurve")
        self.curve.getShape().attr("worldSpace[0]") >> node.inputCurve
        node.addAttr("branch_node", at="message")
        self.node.nearestPointOnCurve >> node.branch_node
        # remapValue for scale function
        node = pc.createNode("remapValue")
        self.node.u_value >> node.inputValue
        node.addAttr("branch_node", at="message")
        self.node.remapValue >> node.branch_node
        
    @property
    def curve(self):
        return self.node.curve.listConnections()[0]
    @curve.setter
    def curve(self, crv):
        crv.message >> self.node.curve
        
    @property
    def density(self):
        return self.node.density.get()
    @density.setter
    def density(self, value):
        self.node.density.set(value)
    
    @property
    def attach_threshold(self):
        return self.node.attach_threshold.get()
    @attach_threshold.setter
    def attach_threshold(self, value):
        self.node.attach_threshold.set(value)
        
    @property
    def length(self):
        return self.node.curveInfo.listConnections()[0].arcLength.get()
        
    @property
    def u(self):
        return self.node.u_value.get()
    @u.setter
    def u(self, u):
        self.node.u_value.set(u)
        
    @property
    def pos(self):
        return self.node.pointOnCurveInfo.listConnections()[0].position.get()
    
    @property
    def start_pos(self):
        return self.curve.getShape().cv[0].getPosition()

    @property
    def parent_u_pos(self):
        self.node.parent_u_pos.get()
    @parent_u_pos.setter
    def parent_u_pos(self, u_pos):
        self.node.parent_u_pos.set(u_pos)

    @property
    def parent(self):
        connections = self.node.parent_branch.listConnections()
        if not connections:
            return None
        return self.branch_manager._branch_map[connections[0]]
        
    def __str__(self):
        return self.node.name()
        
    def __repr__(self):
        return self.node.name()


class BranchManager:
    def __init__(self, node=None, name="branches", density=5, attach_threshold=0.6):
        self._branch_map = {}
        if not node:
            self.name = name
            self._create_main_node()
            self.density = density
            self.attach_threshold = attach_threshold
        else:
            self.node = node

    def _create_main_node(self):
        self.node = pc.createNode("network", n=f"{self.name}_branchManager")
        self.node.addAttr("density", at="float")
        self.node.addAttr("attach_threshold", at="float")
        self.node.addAttr("branches", at="message")

    def add_curve(self, curve):
        if curve in self.list_curves():
            return
        branch = Branch(self, curve=curve)
        self.node.branches >> branch.node.branch_manager_node
        self._branch_map[branch.node] = branch

    def add_curves(self, curves):
        for curve in curves:
            self.add_curve(curve)

    def check_relationship(self):
        for branch1 in self._branch_map.values():
            for branch2 in self._branch_map.values():
                branch1.check_relationship(branch2)

    def get_start_branch(self):
        branches_without_parent = [r for r in self._branch_map.values() if r.parent is None]
        if len(branches_without_parent) == 1:
            return branches_without_parent[0]

    def get_positions(self):
        start_branch = self.get_start_branch()
        if start_branch is None:
            pc.warning("There is no or more than one startbranch.")
            return []
        return start_branch.recurse_positions()
            
    def list_curves(self):
        return [b.curve for b in self.node.branches.listConnections()]


sel = pc.selected()   

bm = BranchManager()
bm.add_curves(sel)
bm.check_relationship()
# p_transform, p_shape = pc.nParticle(p=bm.get_positions(), c=1)
# p_shape.addAttr("radiusPP", dt="doubleArray")
# p_shape.addAttr("radiusPP0", dt="doubleArray")





class Root:
    def __init__(self, node=None, curve=None, density=5, attach_threshold=0.6):
        self._positions = []
        if not node:
            self.create_node(curve=curve, density=density, attach_threshold=attach_threshold)
        else:
            self.node = node
            self.read_node()
        
        self._branches = {}
        self._parent_branch = None
        self.startpoint = pc.datatypes.Vector(self.curve_shape.cv[0].getPosition())
        self.start_size = 1
        self.calc_positions()
        
    def read_node(self):
        self.positions = [pc.datatypes.Vector(p) for p in json.loads(self.node.positions.get())]
    
    def create_node(self, curve, density=5, attach_threshold=0.6):
        curve.getShape().overrideEnabled.set(True)
        self.node = pc.createNode("network")
        self.node.addAttr("curve", at="message")
        self.node.addAttr("rooter_node", at="message")
        self.node.addAttr("density", at="float")
        self.node.addAttr("attach_threshold", at="float")
        self.node.addAttr("positions", dt="string")
        self.node.addAttr("branches", at="message")
        self.node.addAttr("parent_branch", at="message")
        self.node.addAttr("parent_pos_index", at="long")
        
        self.density = density
        self.attach_threshold = attach_threshold
        if curve:
            self.curve = curve
    
    def calc_positions(self):
        len_node = pc.createNode("curveInfo")
        self.curve_shape.attr("worldSpace[0]") >> len_node.inputCurve
        crv_len = len_node.arcLength.get()
        num_positions = int(self.density * crv_len)
        step_size = 1 / num_positions
        pos_node = pc.createNode("pointOnCurveInfo")
        pos_node.turnOnPercentage.set(True)
        positions = []
        self.curve_shape.attr("worldSpace[0]") >> pos_node.inputCurve
        for i in range(num_positions):
            pos_node.parameter.set(i * step_size)
            positions.append(pos_node.position.get())
        pc.delete(len_node, pos_node)
        self.positions = positions

    def detect_parents(self):
        self.rooter_node.roots
        
    def detect_branches(self, all_roots):
        for root in all_roots:
            if root == self:
                continue
            for i, pos in enumerate(self.positions):
                if pos.distanceTo(root.startpoint) < self.attach_threshold:
                    self.add_branch(root, i)
                    break

    def add_branch(self, root, index):
        root.parent_branch = self
        root.parent_pos_index = index
        self._branches[index] = root
        colorize(root.curve, [0, 0.8, 0.1])

    def get_positions(self):
        pos = [list(p) for p in self.positions]
        for root in self._branches.values():
            pos.extend(root.get_positions())
        return pos

    def get_radius(self):
        scale = 1.0
        if self.parent_branch:
            scale = self.parent_branch.get_scale_at_index(self.parent_pos_index)
        rooter_node = self.node.rooter_node.listConnections()[0]
        radius_map = rooter_node.radius_map.listConnections()[0]
        num_positions = len(self.positions)
        step = 1.0 / num_positions
        radii = []
        for i in range(num_positions):
            radius_map.inputValue.set(i * step)
            radii.append(radius_map.outValue.get() * scale)
        for root in self._branches.values():
            radii.extend(root.get_radius())
        return radii
    
    def set_rooter_node(self, rooter_node):
        rooter_node.roots >> self.node.rooter_node

    def get_scale_at_index(self, index):
        rooter_node = self.node.rooter_node.listConnections()[0]
        radius_map = rooter_node.radius_map.listConnections()[0]
        num_positions = len(self.positions)
        step = 1.0 / num_positions
        radius_map.inputValue.set(index * step)
        return radius_map.outValue.get()
    
    @property
    def curve(self):
        crv = self.node.curve.listConnections()
        if crv:
            return crv[0]
    @curve.setter
    def curve(self, crv):
        crv.message >> self.node.curve
        
    @property
    def curve_shape(self):
        return self.curve.getShape()
        
    @property
    def density(self):
        return self.node.density.get()
    @density.setter
    def density(self, d):
        self.node.density.set(d)
        
    @property
    def attach_threshold(self):
        return self.node.attach_threshold.get()
    @attach_threshold.setter
    def attach_threshold(self, at):
        self.node.attach_threshold.set(at)

    @property
    def positions(self):
        if self._positions:
            return self._positions
        pos_string = self.node.positions.get()
        if not pos_string:
            return []
        return [pc.datatypes.Vector(p) for p in json.loads(pos_string)]
    @positions.setter
    def positions(self, positions:List[pc.datatypes.Vector]):
        self.node.positions.set(
            json.dumps([list(p) for p in positions])
        )
        self._positions = positions

    @property
    def parent_branch(self):
        if self._parent_branch:
            return self._parent_branch
        parent_node_inputs = self.node.parent_branch.listConnections()
        if not parent_node_inputs:
            return None
        root = self.rooter_node.root_map[parent_node_inputs[0]]
        self._parent_branch = root
        return root
    @parent_branch.setter
    def parent_branch(self, root):
        self._parent_branch = root
        root.node.branches >> self.node.parent_branch

    @property
    def parent_pos_index(self):
        return self.node.parent_pos_index.get()
    @parent_pos_index.setter
    def parent_pos_index(self, index):
        self.node.parent_pos_index.set(index)

               
class Rooter:
    def __init__(self, rooter_node=None, density=2, attach_threshold=0.75):
        self.roots = []
        self.root_map = {}
        self._start_root = None
        self.density = density
        self.attach_threshold = attach_threshold
        self._radius_map = None
        if rooter_node:
            self.rooter_node = rooter_node
            self.read_rooter_node()
        else:
            self.rooter_node = self.create_rooter_node()
        
        
    def add_curve(self, curve):
        if curve in self.list_curves():
            return
        root = Root(curve=curve, density=self.density, attach_threshold=self.attach_threshold)
        root.set_rooter_node(self.rooter_node)
        self.roots.append(root)
           
    def create_rooter_node(self):
        rooter_node = pc.createNode("network")
        rooter_node.addAttr("roots", at="message")
        rooter_node.addAttr("start_root", at="message")
        rooter_node.addAttr("radius_map", at="message")
        radius_map = pc.createNode("remapValue")
        radius_map.message >> rooter_node.radius_map
        return rooter_node
        
    def read_rooter_node(self):
        for rn in self.root_nodes:
            root = Root(node=rn)
            self.roots.append(root)
            self.root_map[rn] = root

    def add_curves(self, curves):
        for c in curves:
            self.add_curve(c)
            
    def detect_branches(self):
        for root in self.roots:
            root.detect_branches(self.roots)
        self.start_root = self.get_start_root()
        if self.start_root is None:
            roots = [root for root in self.roots if root._parent_branch is None]
            for root in roots:
                colorize(root.curve, [0.8, 0, 0])


    def get_positions(self):
        return self.start_root.get_positions()
    
    def get_radius(self):
        return self.start_root.get_radius()
        
    def list_curves(self):
        return [r.curve for r in self.roots]

    def get_start_root(self):
        start_roots = [root for root in self.roots if root._parent_branch is None]
        if len(start_roots) == 1:
            return start_roots[0]
            
    @property
    def root_nodes(self):
        return self.rooter_node.roots.listConnections()
    
    @property
    def start_root(self):
        if self._start_root is not None:
            return self._start_root
        sr_nodes = self.rooter_node.start_root.listConnections()
        if sr_nodes:
            self._start_root = self.root_map[sr_nodes[0]]
            return self._start_root
    @start_root.setter
    def start_root(self, root):
        if root is None:
            return
        self._start_root = root
        root.node.message >> self.rooter_node.start_root

          
# from capito.maya.geo.generators import Rooter

# curves = pc.selected()
# r = Rooter()
# r.add_curves(curves)
# r.detect_branches()

# p_transform, p_shape = pc.nParticle(p=r.get_positions(), c=1)
# p_shape.addAttr("radiusPP", dt="doubleArray")
# p_shape.addAttr("radiusPP0", dt="doubleArray")

# base_radius = 2.0
# for i, radius_scale in enumerate(r.get_radius()):
#     pc.nParticle(p_shape, e=1, id=i, at="radiusPP",floatValue=base_radius * radius_scale)
    




def stone(face_count=60, base_objects=5, name="stone"):
    objects = [pc.polySphere(sx=12, sy=12)[0] for _ in range(base_objects)]
    #objects = [pc.polyCube(sw=4, sd=4, sh=4)[0] for _ in range(base_objects)]

    for obj in objects:
        trans_rand = [uniform(-1, 1) for _ in range(3)]
        rot_rand = [uniform(-180, 180) for _ in range(3)]
        scale_rand = [uniform(0.5, 1.5) for _ in range(3)]
        obj.setTranslation(trans_rand)
        obj.setRotation(rot_rand)
        obj.setScale(scale_rand)
        
    stone_transform = pc.polyCBoolOp(objects, op=1, ch=0)
    pc.polyRemesh(stone_transform, ch=0)
    pc.polyAverageVertex(stone_transform, i=5, ch=0)
    pc.polyAverageVertex(stone_transform, i=5, ch=0)
    pc.polyRetopo(stone_transform, targetFaceCount=face_count, ch=0)
    pc.select(stone_transform)
    dupe = pc.duplicate()[0]
    bb_min = dupe.boundingBoxMin.get()
    bb_max = dupe.boundingBoxMax.get()
    bb_size = [max - min for max, min in zip(bb_max, bb_min)]
    dupe.setScale([1/val for val in bb_size])
    pc.xform(dupe, cpc=True)
    dupe.setTranslation([-v for v in dupe.rotatePivot.get()])
    pc.makeIdentity(dupe, apply=True)
    sculpt, sculptor, origin = pc.sculpt()
    sculptor.setScale([3,3,3])
    pc.delete(dupe, ch=True)
    pc.select(dupe.faces)
    pc.polyProjection(ch=0, type="Spherical")
    pc.select(dupe.map)
    pc.u3dUnfold()
    pc.polyNormalizeUV(
        dupe, normalizeType=1, preserveAspectRatio=0,
        centerOnTile=1, normalizeDirection=0
    )
    pc.select(dupe, stone_transform)
    pc.transferAttributes(
        transferPositions=0, transferNormals=0, transferUVs=2, transferColors=0,
        sampleSpace=5, sourceUvSpace="map1", targetUvSpace="map1",
        searchMethod=3, flipUVs=0, colorBorders=1
    )
    pc.delete(stone_transform, ch=True)
    pc.delete(dupe)

    stone_shape = stone_transform[0].getShape()

    stone_shape.aiSubdivType.set(1)
    stone_shape.aiSubdivIterations.set(3)

    return stone_transform[0]


def stone_shader(name="stone"):
    sg = pc.createNode("shadingEngine", name=f"{name}SG")
    displace = pc.createNode("displacementShader", name=f"{name}_displace")
    ais = pc.createNode("aiStandardSurface", name=f"{name}_ai")
    noise = pc.createNode("aiCellNoise", name=f"{name}_cellnoise")
    displace.displacement >> sg.displacementShader
    ais.outColor >> sg.surfaceShader
    noise.outColorR >> displace.displacement

    displace.aiDisplacementZeroValue.set(0.5)
    noise.pattern.set(5)
    noise.octaves.set(5)
    noise.lacunarity.set(4)

    return sg


def stones(num_stones=10, name="stone"):
    sg = stone_shader(name=name)
    print(sg)
    for i in range(num_stones):
        try:
            s = stone(name=f"{name}_{i}")
            stone_shape = s.getShape()
            stone_shape.attr("instObjGroups[0]").disconnect()
            stone_shape.attr("instObjGroups[0]") >> sg.attr(f"dagSetMembers[{i}]")
        except:
            pc.delete(s)