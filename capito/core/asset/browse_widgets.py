"""The widget for Asset Browsing"""
import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import List

import capito.core.event as capito_event
from capito.conf.config import CONFIG
from capito.core.asset.browse_asset_widgets import (
    CreateAssetsWindow,
    SearchableFilteredAssetList,
)
from capito.core.asset.browse_details_widget import DetailsWidget
from capito.core.asset.browse_step_widgets import StepsWidget
from capito.core.asset.browse_version_widgets import VersionWidget
from capito.core.asset.flows import FlowProvider
from capito.core.asset.models import Asset
from capito.core.asset.providers.baseclass import AssetProvider
from capito.core.asset.providers.exceptions import AssetExistsError
from capito.core.asset.providers.FilesystemAssetProvider import FilesystemAssetProvider
from capito.core.asset.providers.GoogleSheetsAssetProvider import (
    GoogleSheetsAssetProvider,
)
from capito.core.asset.utils import best_match, sanitize_asset_name
from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QHLine, QSplitWidget, RichListItem
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QFont  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QIcon, QPixmap, Qt
from PySide2.QtWidgets import QFrame  # pylint:disable=wrong-import-order
from PySide2.QtWidgets import QHBoxLayout, QPushButton, QSplitter, QVBoxLayout, QWidget

CAPITO_ICONS_PATH = Path(CONFIG.CAPITO_BASE_DIR) / "resources" / "icons"


class BrowseToolbar(QWidget):
    """The upper toolbar"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        create_button = QPushButton("Create Asset(s)")
        create_button.clicked.connect(CreateAssetsWindow)
        hbox.addWidget(create_button)
        hbox.addStretch()

        self.setLayout(hbox)


class BrowseWidget(QWidget):
    """The top widget for the BROWSE tab."""

    def __init__(self, host: str):
        super().__init__()
        self.host = host

        self._create_widgets()
        self._connect_widgets()
        self._create_ui()

    def _create_widgets(self):
        self.browse_toolbar = BrowseToolbar()
        self.asset_list = SearchableFilteredAssetList()
        self.steps_widget = StepsWidget(self.host)
        self.version_widget = VersionWidget(self.host)
        self.details_widget = DetailsWidget(self.host)

    def _connect_widgets(self):
        self.asset_list.signals.asset_selected.connect(self.steps_widget.update)
        self.asset_list.signals.asset_selected.connect(
            self.version_widget.version_list.clear()
        )
        self.steps_widget.signals.step_selected.connect(self.version_widget.update)
        self.version_widget.signals.version_selected.connect(self.details_widget.update)
        self.asset_list.signals.asset_selected.connect(self.details_widget.update)

    def _create_ui(self):
        vbox = QVBoxLayout()
        # vbox.addWidget(self.browse_toolbar)
        vsplitter = QSplitter(Qt.Horizontal)
        vsplitter.setHandleWidth(10)
        vsplitter.addWidget(self.asset_list)
        step_version_splitter = QSplitter(Qt.Vertical)
        step_version_splitter.addWidget(self.steps_widget)
        step_version_splitter.addWidget(self.version_widget)
        step_version_splitter.setSizes([200, 700])
        vsplitter.addWidget(step_version_splitter)
        vsplitter.addWidget(self.details_widget)
        vsplitter.setSizes([180, 290, 480])
        vbox.addWidget(vsplitter, stretch=1)
        self.setLayout(vbox)
