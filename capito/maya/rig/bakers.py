import math
from typing import List

import pymel.core as pc


def get_axis_name(vector_list:List[int]):
    names = ["rx", "ry", "rz"]
    for i, name in zip(vector_list, names):
        if i:
            return name


def roll_wheel(
    wheel: pc.nodetypes.Transform,
    wheel_radius: float,
    rotation_axis: List[int],
    startframe: float,
    endframe: float,
):
    """Rolls 'wheel' of radius 'wheel_radius'
    around 'rotation_axis' (1,0,0) or (0,1,0) or (0,0,1)
    based on it's movement in the world x,z plane. (Only flat plane supported.)
    """
    axis_name = get_axis_name(rotation_axis)
    print(axis_name)

    try:
        pc.mel.eval(f'CBdeleteConnection "{wheel.name()}.{axis_name}";')
    except:
        pass

    prev_loc = pc.spaceLocator()
    current_loc = pc.spaceLocator()
    distance_node = pc.createNode("distanceBetween")

    prev_loc.attr("worldMatrix[0]") >> distance_node.inMatrix1
    current_loc.attr("worldMatrix[0]") >> distance_node.inMatrix2

    pc.parentConstraint(wheel, current_loc, skipRotate=("x", "z"))
    pc.parent(current_loc, prev_loc)

    pc.currentTime(startframe - 1)
    pc.parentConstraint(wheel, prev_loc, skipRotate=("x", "z"))
    for i in range(startframe, endframe + 1):
        pc.currentTime(i)
        distance = distance_node.distance.get()
        direction = math.copysign(1, current_loc.tz.get())
        delta_rot = math.degrees(distance * math.pi) / (4 * wheel_radius)
        wheel.attr(axis_name).set(
            wheel.attr(axis_name).get() + delta_rot * direction
        )
        pc.setKeyframe(wheel.attr(axis_name))
        pc.delete(pc.parentConstraint(wheel, prev_loc, skipRotate=("x", "z")))

    pc.delete(prev_loc, current_loc, distance_node)


def point_in_movement_direction(
    obj: pc.nodetypes.Transform,
    aim_axis: List[int],
    up_axis: List[int],
    startframe: float,
    endframe: float,
):
    """Points an object in the direction it is moving towards.
    The pointing direction is determined by 'aim_axis'.
    It will be rotated around 'up_axis'.
    Script will turn object 180° if object travels 'backwards'.
    This means it is not suitable for reverse-gear steering."""
    axis_name = get_axis_name(up_axis)
    try:
        pc.mel.eval(f'CBdeleteConnection "{obj.name()}.{axis_name}";')
    except:
        pass

    point_loc = pc.spaceLocator(p=(0, 0, 0))
    pc.pointConstraint(obj, point_loc, mo=False)
    aim_loc = pc.spaceLocator(p=(0, 0, 0))
    aim_loc.setParent(obj)
    aim_loc.setTranslation(aim_axis)
    aim_loc.setParent(world=True)
    aim_constraint = pc.aimConstraint(
        aim_loc,
        point_loc,
        aimVector=aim_axis,
        upVector=[float(v) for v in up_axis],
        worldUpType="vector",
        worldUpVector=up_axis,
    )

    for i in range(int(startframe), int(endframe)):
        pc.currentTime(i + 1)
        aim_loc.setTranslation(point_loc.getTranslation(space="world"), space="world")
        pc.currentTime(i)
        obj.setRotation(point_loc.getRotation(space="world"), space="world")
        if aim_loc.getTranslation() != point_loc.getTranslation():
            pc.setKeyframe(obj.attr(axis_name))

    pc.delete(aim_constraint, aim_loc, point_loc)
