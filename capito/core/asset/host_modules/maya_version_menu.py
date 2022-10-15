"""The widget for Asset Browsing"""
from functools import partial

import pymel.core as pc
from capito.core.asset.host_modules.maya_utils import open_latest, save_version
from capito.core.asset.models import Asset, Step
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QFont  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QIcon, QPixmap, Qt
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QHBoxLayout,
    QPushButton,
    QWidget,
)


class MayaVersionMenu(QWidget):
    def __init__(self, parent) -> None:
        super().__init__()
        self.parent = parent
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.save_first_version_btn = QPushButton("First Version")
        self.save_first_version_btn.hide()
        self.open_latest_btn = QPushButton("Open Latest")
        self.open_latest_btn.hide()

    def _connect_widgets(self):
        self.parent.parent.signals.version_selected.connect(self._on_version_selected)
        self.parent.signals.step_selected.connect(self._on_step_selected)
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
        open_latest(self.step)

    def _save_first_version(self):
        self.step.new_version("ma", "First Version")
        version = self.step.get_latest_version()
        save_version(version)
        self.save_first_version_btn.hide()
        self.parent.parent.update(version.step)
