"""The Version Menu Widget in Maya"""
from functools import partial
from pathlib import Path
from typing import Union

import pymel.core as pc
from capito.maya.viewport.screenshot import Screenshooter
from capito.core.asset.utils import get_version_by_filename
from capito.core.asset.host_modules.maya.maya_utils import open, save_version
from capito.core.asset.models import Asset, Step, Version
from PySide6 import QtCore  # pylint:disable=wrong-import-order
from PySide6.QtGui import QFont  # pylint:disable=wrong-import-order
from PySide6.QtGui import QColor, QIcon, QPixmap, Qt
from PySide6.QtWidgets import (  # pylint:disable=wrong-import-order
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
        self.screenshot_btn = QPushButton(f"Screenshot")
        self.screenshot_btn.hide()

    def _connect_widgets(self):
        self.parent_widget.signals.version_selected.connect(self._on_version_selected)
        self.parent_widget.signals.step_selected.connect(self._on_step_selected)
        self.screenshot_btn.clicked.connect(self._save_screenshot)

    def _create_layout(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.screenshot_btn)
        self.setLayout(vbox)

    def _on_version_selected(self, version: Version):
        self.screenshot_btn.hide()
        current_version = get_version_by_filename(str(pc.sceneName().name))
        if version == current_version:
            self.screenshot_btn.show()
            self.version = version

    def _on_step_selected(self, step: Step):
        self.screenshot_btn.hide()


    def _save_screenshot(self):
        thumbnail_file = Path(f"{self.version.filepath}.jpg")
        Screenshooter(filepath=thumbnail_file, callback_on_accept=self._update_version_item)

    def _update_version_item(self):
        browse_widget = self.parent_widget.parent_widget
        browse_widget.versions_widget.on_step_selected(self.version.step)
        browse_widget.versions_widget.select_by_name(self.version)
        
