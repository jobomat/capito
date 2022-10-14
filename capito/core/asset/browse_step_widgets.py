"""Module for the Step related Asset Browser Widgets."""
import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import List

import capito.core.asset.ui_constants as ui_constants
import capito.core.event as capito_event
from capito.conf.config import CONFIG
from capito.core.asset.browse_signals import Signals
from capito.core.asset.flows import FlowProvider
from capito.core.asset.models import Asset, Step
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


class StepMenu(QWidget):
    """Menu to add (or later maybe edit?) steps to a specific asset."""

    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 5, 0, 0)
        headline = QLabel("Steps")
        headline.setMinimumHeight(ui_constants.BROWSER_HEADLINE_HEIGHT)
        # headline.setAlignment(Qt.AlignCenter)
        headline.setFont(HeadlineFont())
        hbox.addWidget(headline)
        hbox.addStretch()
        add_step_button = QPushButton("Add Step")
        add_step_button.setMinimumWidth(80)
        add_step_button.setMaximumWidth(80)
        hbox.addWidget(add_step_button)
        self.setLayout(hbox)


class StepItemWidget(QWidget):
    """Presentation Widget for a single Item in the Asset List."""

    def __init__(self, step, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.step = step
        hbox = QHBoxLayout()
        hbox.setContentsMargins(5, 2, 5, 2)
        step_label = QLabel(step)
        step_label.setFont(HeadlineFont())
        hbox.addWidget(step_label)

        self.setLayout(hbox)


class StepList(QListWidget):
    """Step list widget."""

    def __init__(self):
        super().__init__()
        self.asset = None
        self.last_selected_step = None

    def add_item(self, step: Step):
        """Add a RichListItem without hazzle."""
        self.addItem(RichListItem(StepItemWidget(step), self))

    def update(self, asset: Asset):
        """Update the step list to reflect the selected asset."""
        selected = self.currentItem()
        if selected:
            self.last_selected_step = selected.widget.step

        self.clear()
        self.asset = asset

        for i, step in enumerate(asset.steps):
            self.add_item(step)
            if self.last_selected_step == step:
                self.setCurrentRow(i)


class StepsWidget(QWidget):
    """Menu and List concerning steps."""

    def __init__(self, host: str):
        super().__init__()
        self.signals = Signals()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        vbox.addWidget(StepMenu())
        self.step_list = StepList()
        self.step_list.itemSelectionChanged.connect(self._step_selected)
        vbox.addWidget(self.step_list)

        self.setLayout(vbox)

    def update(self, asset: Asset):
        """This method is called when the asset list changes.
        It delegates the update call to the step_list."""
        self.step_list.update(asset)

    def _step_selected(self):
        selected = self.step_list.selectedItems()
        if not selected:
            return
        step = selected[0].widget.step
        asset = self.step_list.asset
        self.signals.step_selected.emit(asset, asset.steps[step], None)
