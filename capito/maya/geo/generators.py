from random import uniform
import pymel.core as pc


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