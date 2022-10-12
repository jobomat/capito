"""Module containing the Version related AssetBrowser widgets."""
import importlib
import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import List

import capito.core.event as capito_event
from capito.conf.config import CONFIG
from capito.core.asset.browse_signals import Signals
from capito.core.asset.flows import FlowProvider
from capito.core.asset.models import Asset, Step, Version
from capito.core.asset.providers.baseclass import AssetProvider
from capito.core.asset.providers.exceptions import AssetExistsError
from capito.core.asset.providers.filesystem import FilesystemAssetProvider
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


class VersionItemWidget(QWidget):
    """Presentation Widget for a single Item in the Version List."""

    def __init__(self, version: Version):
        super().__init__()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(5, 5, 5, 5)

        left_vbox = QVBoxLayout()
        version_label = QLabel(str(version))
        version_label.setFont(HeadlineFont(12))
        icons_path = CONFIG.CAPITO_PROJECT_DIR
        if not icons_path:
            icons_path = CAPITO_ICONS_PATH
        
        version_thumb = Path(version.absolute_path) / f"{version.file}.jpg"
        version_thumb = (
            str(version_thumb)
            if version_thumb.exists()
            else str(Path(icons_path) / f"{version.asset.kind}.svg")
        )
        thumb_pixmap = QPixmap(version_thumb).scaled(
            80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        thumb_label = QLabel()
        thumb_label.setPixmap(thumb_pixmap)
        left_vbox.addWidget(version_label)
        left_vbox.addWidget(thumb_label)
        hbox.addLayout(left_vbox)

        right_vbox = QVBoxLayout()
        date_user_hbox = QHBoxLayout()
        date_label = QLabel(version.date)
        user_label = QLabel(version.user)
        date_user_hbox.addWidget(date_label)
        date_user_hbox.addStretch()
        date_user_hbox.addWidget(user_label)
        right_vbox.addLayout(date_user_hbox)
        comment_label = QLabel(version.comment)
        comment_label.setWordWrap(True)
        right_vbox.addStretch()
        right_vbox.addWidget(comment_label)
        hbox.addLayout(right_vbox)

        self.setLayout(hbox)


class VersionList(QListWidget):
    """Version list widget with thumb and asset name."""

    def __init__(self, host: str):
        super().__init__()
        self.setEditTriggers(QListWidget.EditKeyPressed)
        self.host = host

    def add_item(self, version: Version):
        """Add a RichListItem without hazzle."""
        self.addItem(RichListItem(VersionItemWidget(version), self))

    def update(self, step: Step):
        """Update the list (called via signals)."""
        self.clear()
        for vnum, version in reversed(list(step.versions.items())):
            self.add_item(version)


class VersionMenu(QWidget):
    """Menu bar for versions of a specific step."""

    def __init__(self, host):
        super().__init__()
        self.step = None
        self.signals = Signals()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 5, 0, 0)
        headline = QLabel("Versions")
        # headline.setAlignment(Qt.AlignCenter)
        headline.setFont(HeadlineFont())
        hbox.addWidget(headline)
        hbox.addStretch()
        # add_version_menu(hbox, signals, host)
        # 
        try:
            first_version_module = importlib.import_module(
                f"capito.core.asset.host_modules.{host}_first_version"
            )
            self.first_version_button = first_version_module.FirstVersionButton(
                self.signals.version_added
            )
            hbox.addWidget(self.first_version_button)
        except:
            print(f"No version handling for {host} implemented.")
        self.setLayout(hbox)

    def update(self, step: Step):
        self.step = step
        if hasattr(self, "first_version_button"):
            self.first_version_button.update(step)


class VersionWidget(QWidget):
    def __init__(self, host: str):
        super().__init__()
        self.host = host
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        self.version_menu = VersionMenu(self.host)
        vbox.addWidget(self.version_menu)
        self.version_list = VersionList(self.host)

        self.version_menu.signals.version_added.connect(self.version_list.update)
        self.version_list.setStyleSheet(
            """
            QListWidget::item {background-color:#363636; margin-bottom: 3px;}
            QListWidget::item:hover {background-color:#666666}
            QListWidget::item:selected {background-color:#555555}
            """
        )
        vbox.addWidget(self.version_list)

        self.setLayout(vbox)

    def update(self, asset: Asset, step: Step, version: Version = None):
        """This method is called when the step list selection changes.
        It delegates the update call to the version_list."""
        self.version_list.update(step)
        self.version_menu.update(step)
