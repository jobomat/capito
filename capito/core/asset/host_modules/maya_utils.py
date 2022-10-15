import pymel.core as pc


def save_version(version, typ="mayaAscii"):
    pc.saveAs(version.filepath, type=typ)


def open_latest(step):
    pc.openFile(step.get_latest_version().filepath)
