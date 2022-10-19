"""Module containing the Version related AssetBrowser widgets."""
import imp
import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import List

import capito.core.event as capito_event
from capito.conf.config import CONFIG
from capito.core.asset.browse_signals import Signals
from capito.core.asset.flows import FlowProvider
from capito.core.asset.host_modules.version_actions import version_menu_factory, version_context_actions_factory
from capito.core.asset.models import Asset, Step, Version
from capito.core.asset.providers.baseclass import AssetProvider
from capito.core.asset.providers.exceptions import AssetExistsError
from capito.core.asset.providers.FilesystemAssetProvider import FilesystemAssetProvider
from capito.core.asset.utils import best_match, sanitize_asset_name
from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import HeadlineFont, QHLine, QSplitWidget, RichListItem
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QIcon, QPixmap, Qt, QCursor # pylint:disable=wrong-import-order
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

    def __init__(self, version: Version, parent_widget: QWidget):
        super().__init__()
        self.version = version
        self.parent_widget = parent_widget
        self.icons_path = CONFIG.CAPITO_PROJECT_DIR
        if not self.icons_path:
            self.icons_path = CAPITO_ICONS_PATH

        self._create_widgets()
        self._create_layout()
        self._update_version_item(None)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            partial(self._context_menu, self.version)
        )

    def _create_widgets(self):
        self.version_label = QLabel()
        self.version_label.setFont(HeadlineFont(12))
        self.date_label = QLabel()
        self.user_label = QLabel()
        self.comment_label = QLabel()
        self.comment_label.setWordWrap(True)
        self.thumb_label = QLabel()

    def _create_layout(self):
        hbox = QHBoxLayout()
        hbox.setContentsMargins(5, 5, 5, 5)
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(self.version_label)
        left_vbox.addWidget(self.thumb_label)
        hbox.addLayout(left_vbox)
        right_vbox = QVBoxLayout()
        date_user_hbox = QHBoxLayout()
        date_user_hbox.addWidget(self.date_label)
        date_user_hbox.addStretch()
        date_user_hbox.addWidget(self.user_label)
        right_vbox.addLayout(date_user_hbox)
        right_vbox.addStretch()
        right_vbox.addWidget(self.comment_label)
        hbox.addLayout(right_vbox)
        self.setLayout(hbox)

    def _update_version_item(self, *args):
        self.version_label.setText(str(self.version))
        self.date_label.setText(self.version.date)
        self.user_label.setText(self.version.user)
        self.comment_label.setText(self.version.comment)
        self.thumb_label.setPixmap(self._get_thumb_pixmap())

    def _context_menu(self, version:Version, point: QtCore.QPoint):
        menu = QMenu(self)

        for action in version_context_actions_factory(self):
            menu.addAction(action)

        menu.exec_(QCursor.pos())

    def _test(self, version:Version):
        print(version.comment)

    def _get_thumb_pixmap(self):
        version_thumb = Path(f"{self.version.filepath}.jpg")
        version_thumb = (
            str(version_thumb)
            if version_thumb.exists()
            else str(
                Path(self.icons_path)
                / "flows"
                / "kinds"
                / f"{self.version.asset.kind}.svg"
            )
        )
        return QPixmap(version_thumb).scaled(
            80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )


class VersionList(QListWidget):
    """Version list widget with thumb and asset name."""

    def __init__(self, parent_widget: QWidget):
        super().__init__()
        self.setEditTriggers(QListWidget.EditKeyPressed)
        self.parent_widget = parent_widget
        self.host = self.parent_widget.host
        self.signals = Signals()

    def add_item(self, version: Version):
        """Add a RichListItem without hazzle."""
        self.addItem(RichListItem(VersionItemWidget(version, self), self))

    def update(self, step: Step):
        """Update the list (called via signals)."""
        self.signals.step_selected.emit(step)
        self.clear()
        if not step:
            return
        for _, version in reversed(list(step.versions.items())):
            self.add_item(version)

    def select_by_name(self, version:Version):
        """Select a list item by version number."""
        index = self._getIndex(version)
        self.setCurrentRow(index)

    def _get_version_widget(
        self, version: Version
    ) -> VersionItemWidget:  # pylint: disable=invalid-name
        """Helper method to get the widget containing the version item."""
        for item in self._iterAllItems():
            if version == item.widget.version:
                return item.widget

    def _iterAllItems(self) -> RichListItem:  # pylint: disable=invalid-name
        for i in range(self.count()):
            yield self.item(i)

    def _getIndex(self, wanted_item: Version) -> int:  # pylint: disable=invalid-name
        """Helper method to get the index of a specific item."""
        for i, item in enumerate(self._iterAllItems()):
            if wanted_item.version == item.widget.version.version:
                return i

    def _update_version_widget(self, version: Version):
        widget = self._get_version_widget(version)
        widget._update_version_item()


class VersionMenu(QWidget):
    """Menu bar for versions of a specific step."""

    def __init__(self, parent_widget: QWidget):
        super().__init__()
        self.parent_widget = parent_widget
        self.step = None
        self.signals = Signals()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 5, 0, 0)
        headline = QLabel("Versions")
        headline.setFont(HeadlineFont())
        hbox.addWidget(headline)
        hbox.addStretch()
        host_specific_widget = version_menu_factory(self)
        hbox.addWidget(host_specific_widget)

        self.setLayout(hbox)

    def update(self, step: Step):
        if not step:
            return
        self.step = step
        self.signals.step_selected.emit(step)


class VersionWidget(QWidget):
    """Widget for listing Verions"""

    def __init__(self, parent_widget: QWidget):
        super().__init__()
        self.parent_widget = parent_widget
        self.host = self.parent_widget.host
        self.signals = Signals()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        self.version_menu = VersionMenu(self)
        vbox.addWidget(self.version_menu)
        self.version_list = VersionList(self)
        self.version_list.itemSelectionChanged.connect(self._selection_changed)

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
        capito_event.subscribe(
            "version_changed", self.version_list._update_version_widget
        )

    def update(self, step: Step):
        """This method is called when the step list selection changes.
        It delegates the update call to the version_list and menu."""
        self.version_list.update(step)
        self.version_menu.update(step)

    def _selection_changed(self):
        item = self.version_list.currentItem()
        if item:
            self.signals.version_selected.emit(item.widget.version)

    def select_by_name(self, version:Version):
        if version:
            self.version_list.select_by_name(version)
