"""Module containing the Version related AssetBrowser widgets."""
import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import List

import capito.core.asset.ui_constants as ui_constants
import capito.core.event as capito_event
from capito.conf.config import CONFIG
from capito.core.asset.flows import FlowProvider
from capito.core.asset.models import Asset, Step, Version
from capito.core.asset.providers.baseclass import AssetProvider
from capito.core.asset.providers.exceptions import AssetExistsError
from capito.core.asset.providers.FilesystemAssetProvider import FilesystemAssetProvider
from capito.core.asset.utils import best_match, sanitize_asset_name
from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import HeadlineFont, QHLine, QSplitWidget, RichListItem
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QFont  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QIcon, QPixmap, Qt
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QAbstractItemView,
    QAction,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabBar,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

CAPITO_ICONS_PATH = Path(CONFIG.CAPITO_BASE_DIR) / "resources" / "icons"


class DetailsWidget(QWidget):
    """Widget for showing all Details for a selected Version."""

    def __init__(self, host):
        super().__init__()
        self.host = host

        self._create_widgets()
        self._create_ui()

    def update(self, version: Version):
        """On selection change..."""
        asset_name = ""
        step = ""
        kind = ""
        if version:
            asset_name = version.asset.name
            step = version.step.name
            kind = version.asset.kind
        self.asset_name.setText(asset_name)
        self.step.setText(step)
        self.kind.setText(kind)

    def _create_widgets(self):
        self.asset_name = QLabel("")
        self.asset_name.setFont(HeadlineFont())
        self.kind = QLabel("")
        self.kind.setFont(HeadlineFont())
        self.step = QLabel("")

    def _create_ui(self):
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        headline_hbox = QHBoxLayout()
        headline_hbox.setContentsMargins(0, 5, 0, 0)
        headline = QLabel("Details")
        headline.setMinimumHeight(ui_constants.BROWSER_HEADLINE_HEIGHT)
        # headline.setAlignment(Qt.AlignCenter)
        headline.setFont(HeadlineFont())
        headline_hbox.addWidget(headline)

        vbox.addLayout(headline_hbox)

        vbox.addWidget(self.asset_name)
        vbox.addWidget(self.kind)
        vbox.addWidget(self.step)

        vbox.addStretch()
        self.setLayout(vbox)
