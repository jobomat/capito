import pymel.core as pc


def save_version(version, typ="mayaAscii"):
    pc.saveAs(version.filepath, type=typ)


def open(filepath: str):
    pc.openFile(filepath, force=True)
