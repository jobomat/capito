"""The Version Menu Widget in Maya"""
from functools import partial
from pathlib import Path

import pymel.core as pc
from capito.core.asset.utils import get_version_by_filename
from capito.core.asset.host_modules.maya.maya_utils import open, save_version
from capito.core.asset.models import Asset, Step, Version
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QFont  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QIcon, QPixmap, Qt
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DetailActionsWidget(QWidget):
    """Maya specific ui"""

    def __init__(self, parent_widget) -> None:
        super().__init__()
        self.parent_widget = parent_widget
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.save_version_btn = QPushButton(f"Save Version")
        self.save_version_btn.hide()

    def _connect_widgets(self):
        self.parent_widget.signals.version_selected.connect(self._on_version_selected)
        self.save_version_btn.clicked.connect(self._save_version)

    def _create_layout(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.save_version_btn)
        self.setLayout(vbox)

    def _on_version_selected(self, version:Version):
        self.save_version_btn.hide()
        current_version = get_version_by_filename(str(pc.sceneName().name))
        if not version or not current_version:
            return
        is_same_asset = version.asset.name == current_version.asset.name
        is_same_step = version.step.name == current_version.step.name
        if is_same_asset and is_same_step:
            self.save_version_btn.show()
            self.version = version


    def _save_version(self):
        self.version.step.new_version("ma", "TEST")
        version = self.version.step.get_latest_version()
        save_version(version)
        self.parent_widget.parent_widget.version_widget.update(version.step)
        self.parent_widget.parent_widget.version_widget.select_by_name(version)
        
