"""The Version Menu Widget in Maya"""
from functools import partial
from pathlib import Path
import re
from capito.conf.config import CONFIG

VERSION_REGEX = re.compile(r"\{(.*?)\}")
VERSION_KEYS = VERSION_REGEX.findall(CONFIG.VERSION_FILE)

import pymel.core as pc
from capito.core.asset.host_modules.maya_utils import open, save_version
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
        
        self.clicked.connect(self._reveal)

    def _reveal(self):
        scene_name = str(pc.sceneName().name)
        try:
            value_string, extension = scene_name.split(".")
            values = value_string.split("_")
            values.append(extension)

            map = {k: v for k, v in zip(VERSION_KEYS, values)}

            self.parent_widget.signals.reveal_clicked.emit(
                map["asset"], map["step"], map["version"]
            )
        except:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Current scene is not part of the project.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

