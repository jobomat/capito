from maya.api import OpenMaya as om
from random import uniform
import pymel.core as pc


def get_unused_shapes(transform):
    return [s for s in transform.getShapes() if not s.listConnections()]


def get_used_shapes(transform):
    return [s for s in transform.getShapes() if s.listConnections()]


def delete_unused_shapes(transform):
    pc.delete(get_unused_shapes(transform))


def add_shapes(from_obj: pc.nodetypes.Transform, to_obj: pc.nodetypes.Transform):
    """Adds shapes found in from_obj to to_obj."""
    for shape in from_obj.getShapes():
        pc.parent(shape, to_obj, shape=True, add=True)


def randomize_components(components, mini=(-0.1, -0.1, -0.1), maxi=(0.1, 0.1, 0.1), space="object"):
    for comp in components:
        new_pos = [
            pos + uniform(mi, ma)
            for pos, mi, ma
            in zip(comp.getPosition(space=space), mini, maxi)
        ]
        comp.setPosition(new_pos, space=space)
    if components[0].node().type() == "nurbsCurve":
        components[0].node().updateCurve()


def rotate_shapes(transform, amount=(90, 0, 0), pivot=None):
    """
    Rotates the components (shapes) of a given pymel-transform
    transform: The pymel transform which shapes are to rotate
    amount: Degrees to rotate around [x, y, z]
    """
    component_type = ""
    try:
        shapes = transform.getShapes()
        if hasattr(shapes[0], "vtx"):
            component_type = "vtx"
        elif hasattr(shapes[0], "cv"):
            component_type = "cv"
        else:
            pc.warning("Transform Node doesn't contain rotatable shapes.")
            return
    except IndexError:
        pc.warning("Transform Node doesn't contain any shapes.")

    sym = pc.symmetricModelling(q=True)
    pc.symmetricModelling(e=True, symmetry=False)

    pivot = pivot or transform.getAttr("worldMatrix")[3][:-1]
    component_lists = [
        getattr(shape, component_type) for shape in transform.getShapes()
    ]
    for component_list in component_lists:
        pc.rotate(
            component_list, amount, p=pivot,
            r=True, os=True, eu=True
        )
    pc.symmetricModelling(e=True, symmetry=sym)


def set_unrenderable(shapes):
    attributes = [
        "visibleInRefractions", "visibleInReflections", "primaryVisibility", "motionBlur",
        "receiveShadows", "castsShadows", "smoothShading", "aiVisibleInDiffuseReflection",
        "aiVisibleInSpecularReflection", "aiVisibleInDiffuseTransmission",
        "aiVisibleInSpecularTransmission", "aiVisibleInVolume", "aiSelfShadows"
    ]
    for shp in shapes:
        for attr in attributes:
            if shp.hasAttr(attr):
                shp.setAttr(attr, 0)


def get_symmetry_dict_slow(shape):
    sym_status = pc.symmetricModelling(q=True, symmetry=True)
    pc.symmetricModelling(symmetry=True)
    sym_dict = {}
    for i in range(shape.numVertices()):
        pc.select(shape.vtx[i], symmetry=True)
        pair = [v.index() for v in pc.selected()]
        if len(pair) == 1:
            sym_dict[i] = i
        else:
            sym_dict[i] = [v for v in pair if v != i][0]
    pc.symmetricModelling(symmetry=sym_status)
    return sym_dict


def get_symmetry_dict(transform, mid_tolerance=0.005):
    """Get a dictionary with symmetric vertex information.
    The dictionary key will be a vertex index.
    The dictionary value will be the index of the corresponding symmetric vertex

    It will also work with topological symmetry.
    """
    # For the function to work symmetry in the viewport must be turned on
    sym_status = pc.symmetricModelling(q=True, symmetry=True)
    pc.symmetricModelling(symmetry=True)
    # converting selected object into MObject and MFnMesh functionset
    mSel = om.MSelectionList()
    mSel.add(transform.name())
    mObj = mSel.getDagPath(0)
    mfnMesh = om.MFnMesh(mObj)
    baseShape = mfnMesh.getPoints()  # getting our basePoints
    # this function can be used to revert the object back to the baseShape
    mfnMesh.setPoints(baseShape)
    # getting l and r verts
    mid_tolerance = 0.005  # this will be our mid tolerance, if the mesh is not completely symmetric on the mid
    lVerts = []  # for storing left Verts
    corrVerts = {}  # for storing correspondign verts

    for i in range(mfnMesh.numVertices):  # iteratign through all the verts on the mesh
        thisPoint = mfnMesh.getPoint(i)  # getting current point position
        if thisPoint.x > mid_tolerance:  # if pointValue on x axis is bigger than midTolerance
            # append to left vert storage list(i = vert index, thisPoint = vert Mpoint position)
            lVerts.append((i, thisPoint))
        elif not thisPoint.x < -mid_tolerance:
            # these are the symmetry-edge-verts
            corrVerts[i] = i

    # selecting our verts with symmetry on
    pc.select(["%s.vtx[%s]" % (mObj, i) for i, v in lVerts], sym=True)
    # getting the rich selection. it will store the symmetry iformation for us
    mRichBase = om.MGlobal.getRichSelection()
    # this will store our lSide verts as an MSelectionList
    lCor = mRichBase.getSelection()
    rCor = mRichBase.getSymmetry()  # this will symmetry verts as an MSelectionList
    # creating iterative lists so we can get the components
    mitL = om.MItSelectionList(lCor)
    mitR = om.MItSelectionList(rCor)

    while not mitL.isDone():  # iterating through the left list
        mitLComp = mitL.getComponent()  # getting dag path and components of leftside
        mitRComp = mitR.getComponent()  # getting dag path and components of rightside
        # creating our iterative vertex lists
        mitLCorVert = om.MItMeshVertex(mitLComp[0], mitLComp[1])
        mitRCorVert = om.MItMeshVertex(mitRComp[0], mitRComp[1])

        while not mitLCorVert.isDone():  # iterating through our verts
            # adding corresponding verts to our dictionary
            corrVerts[mitLCorVert.index()] = mitRCorVert.index()
            corrVerts[mitRCorVert.index()] = mitLCorVert.index()
            mitLCorVert.next()  # go to nextb vert. needed to stop loop
            mitRCorVert.next()  # go to next vert. needed to stop loop
        mitL.next()  # go to next selection in list if more. needed to stop loop
        mitR.next()  # go to next selection in list if more. needed to stop loop
    pc.select(cl=1)  # deseleting our verts
    
    #now the corrVerts will have stored the corresponding vertices from left to right
    pc.symmetricModelling(symmetry=sym_status)
    return corrVerts
