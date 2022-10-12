"""The widget for Asset Browsing"""
from functools import partial

import pymel.core as pc
from capito.core.asset.host_modules.maya_utils import save_version
from capito.core.asset.models import Asset, Step
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QFont  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QIcon, QPixmap, Qt
from PySide2.QtWidgets import QPushButton  # pylint:disable=wrong-import-order


class FirstVersionButton(QPushButton):
    def __init__(self, version_added_event):
        super().__init__()
        self.step = None
        self.version_added_event = version_added_event
        self.setText("Save Version 1")
        self.setToolTip(f"Save current scene as first Version.")
        self.clicked.connect(self.save)
        self.hide()

    def update(self, step: Step):
        if step.versions:
            self.hide()
            return
        self.show()
        self.step = step

    def save(self):
        self.step.new_version("ma", "First Version")
        version = self.step.get_latest_version()
        version.save_json()
        self.version_added_event.emit(version.step)
        save_version(version)
        self.hide()
