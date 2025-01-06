import pymel.core as pc


def replace_shape(source: pc.nodetypes.Transform, target: pc.nodetypes.Transform):
    source_shapes = source.getShapes()
    target_shapes = target.getShapes()
    ts_override_enabled = target_shapes[0].overrideEnabled.get()
    ts_color_type = target_shapes[0].overrideRGBColors.get()
    ts_color = target_shapes[0].overrideColor.get()

    for shape in source_shapes:
        pc.parent(shape, target, s=True, add=True, nc=True)
        shape.overrideEnabled.set(ts_override_enabled)
        shape.overrideRGBColors.set(ts_color_type)
        shape.overrideColor.set(ts_color)

    pc.delete(target_shapes)


def mirror_shape(source: pc.nodetypes.Transform, target: pc.nodetypes.Transform, scale=[-1,-1,-1]):
    clone = pc.duplicate(source)[0]
    pc.parent(clone, w=True)
    pc.delete(clone.getChildren(type="transform"))

    # unlock and reset the transform attributes, mirror in x        
    for attr in ["tx","ty","tz","rx","ry","rz","sx","sy","sz"]:
        clone.attr(attr).setLocked(False)

    clone.translate.set([0,0,0])
    clone.rotate.set([0,0,0])
    clone.scale.set(scale)

    pc.parent(clone, w=True)
    pc.makeIdentity(clone, apply=True, s=1, t=1, r=1)

    # try to reconnect mapped attributes of the shapes - only works for simple cases
    t_attrs = target.getShape().listConnections(connections=True, plugs=True)
    for attr, ctrl_attr in t_attrs:
        for shape in clone.getShapes():
            ctrl_attr >> shape.attr(attr.attrName())

    replace_shape(clone, target)
    pc.delete(clone)


def mirror_mgear_controller_shapes(source_side="L", set_name="rig_controllers_grp"):
    try:
        controllers_set = pc.PyNode(set_name)
    except pc.general.MayaNodeError:
        result = pc.confirmDialog(
            title='Please Help...',button=['OK','Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel',
            message="Couldn't find the mgear rig_controllers_grp set.\n Please select the set manually and click 'OK'."
        )
        if result == "OK":
            sel = pc.selected()
            if not sel:
                pc.warning("Nothing selected. Aborting")
            controllers_set = sel[0]
            if not isinstance(controllers_set, pc.nodetypes.ObjectSet):
                pc.warning("The selection must be the rig_controllers_grp set! Aborting.")

    f, t = ("_L", "_R") if source_side == "L" else ("_R", "_L")
    
    left_controllers = [c for c in controllers_set.members() if f in c.name()]
    right_controllers = [pc.PyNode(c.name().replace(f, t)) for c in left_controllers]

    for source, target in zip(left_controllers, right_controllers):
        mirror_shape(source, target)
