# encoding: utf-8
import pymel.core as pc


def get_curve_length(curve: pc.nodetypes.NurbsCurve) -> float:
    """Returns the length of given curve."""
    crv_info = pc.createNode("curveInfo")
    curve.worldSpace >> crv_info.inputCurve
    crv_len = crv_info.arcLength.get()
    pc.delete(crv_info)
    return crv_len


def combine_shapes(transforms, delete=True):
    """
    Takes a list of pymel.nt.Transform nodes. Returns the "combined" transform.
    Adds all nurbsCurve-Shapes to the first Transform node in the list.
    :param transforms: A list containing the nurbsCurve Transforms to be combined (Transforms containing nurbsCurve-Shapes).
    .type transforms: list (containing :class:`pymel.core.nodetypes.Transform`)
    :param delete: If True all but the first (combined) Transform will be deleted.
    :type delete: bool

    :returns: A transform node containing the combined nurbsCurve-Shapes.
    :rtype: :class:`pymel.core.nodetypes.Transform`
    :raises: None
    """
    name = transforms[0].name()

    for i, obj in enumerate(transforms[1:]):
        obj_copy = pc.duplicate(obj)[0]
        pc.parent(obj_copy, world=True, a=True)
        pc.makeIdentity(obj_copy, apply=True)
        for shape in obj_copy.getShapes():
            if shape.type() == "nurbsCurve":
                nurbs_curve = pc.createNode("nurbsCurve")
                transform_geo_node = pc.createNode("transformGeometry")
                shape.worldSpace[0] >> transform_geo_node.inputGeometry
                transforms[0].worldMatrix[0] >> transform_geo_node.transform
                # transform_geo_node.outputGeometry >> nurbs_curve.create
                # written the long way because of annoying pymel warning:
                pc.connectAttr(
                    '{}.outputGeometry'.format(transform_geo_node.name()),
                    '{}.create'.format(nurbs_curve.name())
                )
                transform_geo_node.setAttr("invertTransform", 1)
                pc.delete(nurbs_curve, ch=True)
                nurbs_curve.rename("{}Shape{}".format(name, str(i + 1).zfill(2)))
                pc.parent(nurbs_curve, transforms[0], add=True, shape=True)
                pc.delete(nurbs_curve.getParent())
        pc.delete(obj_copy)

    if delete:
        pc.delete(transforms[1:])
    return transforms[0]


def replace_shapes(transforms, keep_position=False):
    """
    Replaces all nurbsCurve Shapes found in transforms[0] with all nurbsCurve Shapes found in transforms[1:]

    :param transforms: A List containing the transforms where all nurbsCurve shapes in item 0 will be replaced with all nurbsCurve shapes found in items 1 to end of list.
    :type transforms: list (containing :class:`pymel.core.nodetypes.Transform`)
    :param keep_position: If True the replacing shapes will not be moved in space.
    :type keep_position: bool

    :returns: None
    :rtype: None
    :raises: None
    """
    for shape in transforms[0].getShapes():
        if shape.type() == "nurbsCurve":
            pc.delete(shape)
    if not keep_position:
        for transform in transforms[1:]:
            constraint = pc.parentConstraint(transforms[0], transform, mo=False)
            pc.delete(constraint)
    combine_shapes(transforms)


def read_shapes(transform, name=""):
    """
    Takes a pymel.Transform and reads info about all nurbsCurve-Shapes contained in transform.
    The resulting datastructure can be used to recreate the nurbsCurves with function 'createCurves'.

    :param transform: The transform containing nurbsCurve-Shapes
    :type transform: :class:`pymel.core.nodetypes.Transform`
    :param name: Name to be set for later generated nurbsCurve-Shapes.
    :type name: str

    :returns: A list of dictionaries. One dict for each nurbsCurve-Shape.
    :rtype: List[
        {name (str), cvs (list), knots (list), degree (int)}
        ...
    ]
    :raises: None
    """
    curves = []
    for shape in transform.getShapes():
        if shape.type() == "nurbsCurve":
            curves.append(
                {
                    'name': name if name != "" else shape.name(),
                    'cvs': [[cv.x, cv.y, cv.z] for cv in shape.getCVs()],
                    'knots': shape.getKnots(),
                    'degree': shape.degree()
                }
            )
    return curves


def create_curve(curve_dict, offset=[0, 0, 0], name=""):
    """
    Creates a nurbsCurve according to the given dict. (Dict structure created by read_shapes)

    :param curve_dict: The dictionary containing the information about the nurbsCurve to create.
    :type curve_dict: dict {name (str), cvs (list), knots (list), degree (int)}
    :param offset: An translation offset applied to the created cvs.
    :type offset: list

    :returns: A transform node containing the created nurbsCurve-Shape.
    :rtype: :class:`pymel.core.nodetypes.Transform`
    :raises: None
    """
    return pc.curve(
        name=name if name else curve_dict['name'],
        d=curve_dict['degree'],
        k=curve_dict['knots'],
        p=[[x + y for x, y in zip(c, offset)] for c in curve_dict['cvs']]
    )


def create_curves(curve_list, offset=[0, 0, 0], name=""):
    """
    Takes a list of dicts containing info about a nurbsCurve (see createCurve).
    Creates a nurbsCurve out of each dict-info.

    :param curve_list: A list containing dictionaries to use with function 'create_curve'.
    :type curve_list: list
    :param offset: An translation offset applied to the created cvs.
    :type offset: list
    :param name: Name to be set for later generated nurbsCurve-Shapes.
    :type name: str

    :returns: A list of  transform nodes containing the created nurbsCurve-Shape.
    :rtype: list
    :raises: None
    """
    transforms = []
    for curve_dict in curve_list:
        transforms.append(
            create_curve(curve_dict, offset=offset, name=name)
        )
    return transforms


def curve_type(text="Testtext", fontdict=None,
               spacewidth=0.2, kerning=0.025, availableLetters=None):
    """
    Creates nurbsCurves for each character in text.

    :param text:
    :type text:
    :param fontdict:
    :type fontdict: dict {"letter": curve_list}
    :param spacewidth:
    :type spacewidth:
    :param kerning:
    :type kerning:
    :param availableLetters:
    :type availableLetters:

    :returns: A transform node containing the combined created nurbsCurve-Shapes.
    :rtype: :class:`pymel.core.nodetypes.Transform`
    :raises: None
    """
    if fontdict is None:
        import curve_fonts.INPUT as FN
        fontdict = FN.INPUT
    availableLetters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    pos = 0.0
    text_curves = []
    for i, char in enumerate(text):
        if char not in [x for x in availableLetters]:
            char = " "
        if char == " ":
            pos += spacewidth
            continue
        t = create_curves(fontdict[char], name="{}_{}".format(char, i))
        t = combine_shapes(t)
        t.setTranslation([pos, 0, 0])
        text_curves.append(t)
        pos = t.getAttr("boundingBoxMaxX") + kerning
    t = combine_shapes(text_curves)
    t.rename("{}_crv".format(text))
    return t
