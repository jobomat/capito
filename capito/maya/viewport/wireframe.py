import pymel.core as pc


def colorize(transform: pc.nodetypes.Transform, color=[1, 0, 0]):
    """
    Takes a pymel Transform and colors Maya-viewport-wireframes with 'color'.
    Parameter color can be of type list [r, g, b] or int (maya-color-index)
    Works on PolyMeshes, NURBS-Curves, Cameras.
    """
    is_rgb = isinstance(color, (tuple, list))
    color_attribute = "overrideColorRGB" if is_rgb else "overrideColor"
    for shape in transform.getShapes():
        shape.setAttr("overrideEnabled", 1)
        shape.setAttr("overrideRGBColors", is_rgb)
        shape.setAttr(color_attribute, color)
