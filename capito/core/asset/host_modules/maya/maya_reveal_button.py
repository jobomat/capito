"""The Version Menu Widget in Maya"""
from functools import partial
from pathlib import Path
import re
from capito.conf.config import CONFIG

import pymel.core as pc
from capito.core.asset.utils import get_version_by_filename
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


class RevealButton(QPushButton):
    """Maya specific ui"""

    def __init__(self, parent_widget) -> None:
        super().__init__()
        self.parent_widget = parent_widget
        self.setText("Reveal current")
        self.setToolTip("Show details of currently opened asset version.")
        
        self.clicked.connect(self._reveal)

    def _reveal(self):
        scene_name = str(pc.sceneName().name)
        if scene_name:
            version = get_version_by_filename(scene_name)
            if version:
                self.parent_widget.signals.reveal_clicked.emit(version)
                return
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Current scene is not part of the project.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

