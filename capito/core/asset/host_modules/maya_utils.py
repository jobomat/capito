import pymel.core as pc


def save_version(version, typ="mayaAscii"):
    pc.saveAs(version.filepath, type=typ)
