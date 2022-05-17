import math
from typing import List

import pymel.core as pc


def roll_wheel(
    wheel: pc.nodetypes.Transform,
    wheel_radius: float,
    rotation_axis: str,
    startframe: float,
    endframe: float,
):
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
        wheel.attr(rotation_axis).set(
            wheel.attr(rotation_axis).get() + delta_rot * direction
        )
        pc.setKeyframe(wheel.attr(rotation_axis))
        pc.delete(pc.parentConstraint(wheel, prev_loc, skipRotate=("x", "z")))

    pc.delete(prev_loc, current_loc, distance_node)


# sel = pc.selected()

# rotation_axis = "rx"
# wheel_radius = 3.3

# for wheel in sel:
#     pc.mel.eval(f'CBdeleteConnection "{wheel.name()}.{rotation_axis}";')
#     roll_wheel(
#         wheel, wheel_radius, rotation_axis,
#         startframe=int(pc.playbackOptions(q=True, min=True)),
#         endframe=int(pc.playbackOptions(q=True, max=True))
#     )


def point_in_movement_direction(
    obj: pc.nodetypes.Transform,
    aim_axis: List[float],
    up_axis: List[float],
    startframe: float,
    endframe: float,
):
    for axis in "xyz":
        pc.mel.eval(f'CBdeleteConnection "{obj.name()}.r{axis}";')

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

    for i in range(startframe, endframe):
        pc.currentTime(i + 1)
        aim_loc.setTranslation(point_loc.getTranslation(space="world"), space="world")
        pc.currentTime(i)
        obj.setRotation(point_loc.getRotation(space="world"), space="world")
        if aim_loc.getTranslation() != point_loc.getTranslation():
            for axis in ("rx", "ry", "rz"):
                pc.setKeyframe(obj.attr(axis))

    pc.delete(aim_constraint, aim_loc, point_loc)


# sel = pc.selected()
# aim_axis = [0, 0, 1]
# up_axis = [0, 1, 0]
# startframe = int(pc.playbackOptions(q=True, min=True))
# endframe = int(pc.playbackOptions(q=True, max=True))

# for obj in sel:
#     point_in_movement_direction(obj, aim_axis, up_axis, startframe, endframe)
