from functools import partial
from pathlib import Path
from PySide2.QtWidgets import QAction, QMessageBox
from capito.core.asset.host_modules.maya.maya_utils import open


def open_from_context_menu(version):
    if not Path(version.filepath).exists():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("File not found in local asset folder:")
        msg.setInformativeText(f"{version.file}")
        msg.setWindowTitle("File missing")
        msg.setDetailedText(
            f"The file {version.file}\ndoes not exist in your local assets folder ({version.relative_path}).\n\nMaybe you are getting your asset information from an online source (Google Sheets, REST-API) and your local file-base is not up to date.\n\nTo fix this get the file\n{version.file}\nand the corresponding JSON File (e.g. via Nextcloud)\nand place them in the folder\n{version.absolute_path}"
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        return
    open(version.filepath)


def version_context_actions(parent_widget):
    actions = []
    open_action = QAction("Open")
    open_action.triggered.connect(partial(open_from_context_menu, parent_widget.version))
    actions.append(open_action)
    return actions
    