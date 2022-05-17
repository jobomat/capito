from typing import List
import pymel.core as pc


def place_along_curve(objects: List[pc.nodetypes.Transform],
                      curve: pc.nodetypes.NurbsCurve,
                      front_axis: str="x", up_axis: str="y",
                      up_vector: tuple()=(0,1,0),
                      up_object: pc.nodetypes.Transform=None):
    """Places and orients objects along curve"""
    axis_map = {"x": 0, "y": 1, "z": 2, 0: "x", 1: "y", 2: "z"}
    # calc u steps
    u_step = 1.0 / (len(objects) - 1)
    u_values = [x * u_step for x in range(len(objects))]
    # setup motionPath node
    motion_path = pc.createNode("motionPath")
    curve.worldSpace >> motion_path.geometryPath
    motion_path.fractionMode.set(True)
    motion_path.follow.set(True)
    motion_path.frontAxis.set(axis_map[front_axis])
    
    if up_object:
        motion_path.worldUpType.set(2)
        motion_path.worldUpVector.set(up_vector)
        motion_path.upAxis.set(axis_map[up_axis])
        up_object.attr("worldMatrix[0]") >> motion_path.worldUpMatrix
    
    # Place the objects equidistributed along the curve:
    for obj, u_value in zip(objects, u_values):
        motion_path.uValue.set(u_value)
        obj.setTranslation(motion_path.allCoordinates.get())
        obj.setRotation(motion_path.rotate.get())
    # cleanup
    pc.delete(motion_path)
