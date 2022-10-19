"""The Version Menu Widget in Maya"""
from functools import partial
from pathlib import Path

import pymel.core as pc
from capito.core.asset.host_modules.maya.maya_utils import open, save_version
from capito.core.asset.models import Asset, Step
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QFont  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QIcon, QPixmap, Qt
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QWidget,
)


class VersionMenu(QWidget):
    """Maya specific ui"""

    def __init__(self, parent_widget) -> None:
        super().__init__()
        self.parent_widget = parent_widget
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.save_first_version_btn = QPushButton("First Version")
        self.save_first_version_btn.setMinimumWidth(80)
        self.save_first_version_btn.setMaximumWidth(80)
        self.save_first_version_btn.hide()
        self.open_latest_btn = QPushButton("Open Latest")
        self.open_latest_btn.setMinimumWidth(80)
        self.open_latest_btn.setMaximumWidth(80)
        self.open_latest_btn.hide()

    def _connect_widgets(self):
        self.parent_widget.parent_widget.signals.version_selected.connect(self._on_version_selected)
        self.parent_widget.signals.step_selected.connect(self._on_step_selected)
        self.save_first_version_btn.clicked.connect(self._save_first_version)
        self.open_latest_btn.clicked.connect(self._open_latest)

    def _create_layout(self):
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.open_latest_btn)
        hbox.addWidget(self.save_first_version_btn)
        self.setLayout(hbox)

    def _on_version_selected(self, version):
        self.version = version

    def _on_step_selected(self, step: Step = None):
        self.step = step
        if not step.versions:
            self.open_latest_btn.hide()
            self.save_first_version_btn.show()
        else:
            self.open_latest_btn.show()
            self.save_first_version_btn.hide()

    def _open_latest(self):
        latest_version = self.step.get_latest_version()
        latest_filepath = Path(latest_version.filepath)
        print(latest_filepath)
        if not latest_filepath.exists():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("File not found in local asset folder:")
            msg.setInformativeText(f"{latest_version.file}")
            msg.setWindowTitle("File missing")
            msg.setDetailedText(
                f"The file {latest_version.file}\ndoes not exist in your local assets folder ({latest_version.relative_path}).\n\nMaybe you are getting your asset information from an online source (Google Sheets, REST-API) and your local file-base is not up to date.\n\nTo fix this get the file\n{latest_filepath.name}\nand the corresponding JSON File (e.g. via Nextcloud)\nand place them in the folder\n{latest_version.absolute_path}"
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        if pc.isModified():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("The current file has unsaved changes.")
            msg.setInformativeText("Open anyway?")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            confirm = msg.exec_()
            if confirm != 1024:
                return
        open(str(latest_filepath))

    def _save_first_version(self):
        self.step.new_version("ma", "First Version")
        version = self.step.get_latest_version()
        save_version(version)
        self.save_first_version_btn.hide()
        self.parent_widget.parent_widget.update(version.step)
