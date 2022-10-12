"""Module containing the Asset related Asset Browser Widgets."""
from functools import partial
from pathlib import Path
from typing import List

import capito.core.asset.ui_constants as ui_constants
import capito.core.event as capito_event
from capito.conf.config import CONFIG
from capito.core.asset.browse_signals import Signals
from capito.core.asset.models import Asset
from capito.core.asset.providers.baseclass import AssetProvider
from capito.core.asset.providers.exceptions import AssetExistsError
from capito.core.asset.utils import best_match, sanitize_asset_name
from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import HeadlineFont, RichListItem
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QFont  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QIcon, QPixmap, Qt
from PySide2.QtWidgets import QCheckBox  # pylint:disable=wrong-import-order
from PySide2.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

CAPITO_ICONS_PATH = Path(CONFIG.CAPITO_BASE_DIR) / "resources" / "icons"
FLOWS_PATH = Path(CONFIG.CAPITO_PROJECT_DIR) / "flows" / "kinds"


@bind_to_host
class CreateAssetsWindow(QMainWindow):
    """Window for Asset Creation"""

    def __init__(self, asset_provider: AssetProvider, host: str = None, parent=None):
        super().__init__(parent)
        self.host = host
        self.asset_provider = asset_provider
        self.kinds = asset_provider.flow_provider.kinds
        self.setWindowTitle("Create Assets")
        self._create_widgets()
        self._create_ui()

    def _create_widgets(self):
        self.asset_lineedit = QTextEdit()
        self.asset_lineedit.setPlaceholderText(
            "Enter one Asset name per line.\n\nYou can add a Flow seperated by comma. For example:\nkitchen,set\n\nNames without (or unknown) Flow will use the default Flow specified in the dropdown above."
        )
        self.kind_combobox = QComboBox()
        self.kind_combobox.addItems(self.kinds)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._create_assets)

    def _create_ui(self):
        vbox = QVBoxLayout()

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Default Flow:"))
        top_row.addWidget(self.kind_combobox)
        top_row.addStretch()

        button_row = QHBoxLayout()
        button_row.addWidget(self.close_btn)
        button_row.addWidget(self.ok_btn)

        vbox.addLayout(top_row)
        vbox.addWidget(self.asset_lineedit, stretch=1)
        vbox.addLayout(button_row)
        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def _create_assets(self):
        assets_name_list = [
            l for l in self.asset_lineedit.toPlainText().split("\n") if l
        ]
        default_kind = self.kind_combobox.currentText()
        updated_text_list = []
        already_existing_names = []
        for asset_name in assets_name_list:
            name, *kind = asset_name.split(",")
            name = sanitize_asset_name(name)
            kind = default_kind if not kind else kind[0].strip()
            kind = best_match(kind, self.kinds)
            try:
                self.asset_provider.create_asset(name, kind)
            except AssetExistsError:
                updated_text_list.append(f"{name},{kind}")
                already_existing_names.append(name)
        self.asset_lineedit.setText("\n".join(updated_text_list))
        capito_event.post("asset_created")
        if updated_text_list:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("The following Assets already exist:")
            msg.setInformativeText(", ".join(already_existing_names))
            msg.setWindowTitle("Some Assets not created")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()


class AssetItemWidget(QWidget):
    """Presentation Widget for a single Item in the Asset List."""

    def __init__(self, asset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset = asset
        vbox = QVBoxLayout()
        vbox.setContentsMargins(5, 2, 0, 2)

        hbox = QHBoxLayout()
        asset_label = QLabel(asset.name)
        asset_label.setFont(HeadlineFont())
        thumb_svg = FLOWS_PATH / f"{self.asset.kind}.svg"
        thumb_svg = (
            thumb_svg
            if thumb_svg.exists()
            else CAPITO_ICONS_PATH / "default_kind_thumb.svg"
        )
        thumb_pixmap = QPixmap(str(thumb_svg)).scaled(
            80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        thumb_label = QLabel()
        thumb_label.setPixmap(thumb_pixmap)
        hbox.addWidget(asset_label)
        hbox.addStretch()
        hbox.addWidget(thumb_label)
        vbox.addLayout(hbox)
        self.setLayout(vbox)


class AssetList(QListWidget):
    """Asset list widget with thumb and asset name."""

    def __init__(self, asset_provider: AssetProvider, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QListWidget.EditKeyPressed)
        self.asset_provider = asset_provider
        self.search_text = ""
        self.kind_filters = []
        for asset in asset_provider.list():
            self.add_item(asset)
        capito_event.subscribe("asset_created", self.refresh)

    def add_item(self, asset: Asset):
        """Add a RichListItem without hazzle."""
        self.addItem(
            RichListItem(AssetItemWidget(self.asset_provider.get(asset)), self)
        )

    def update_list(self):
        """Show/Hide list items based on all filters"""
        self.clearSelection()
        for i in range(self.count()):
            item = self.item(i)
            if self.search_text in item.widget.asset.name and (
                not self.kind_filters or item.widget.asset.kind in self.kind_filters
            ):
                item.setHidden(False)
            else:
                item.setHidden(True)

    def change_filter(self, kind: str, add: bool):
        """Add or remove from the kind_filter list."""
        if add and kind not in self.kind_filters:
            self.kind_filters.append(kind)
        elif not add and kind in self.kind_filters:
            self.kind_filters.remove(kind)
        self.update_list()

    def change_search_text(self, search_text: str):
        """Provide this to the LineEdit.textChanged.connect function to filter while typing."""
        self.search_text = search_text.lower()
        self.update_list()

    def refresh(self):
        """Rebuild the whole list."""
        self.clear()
        for asset in self.asset_provider.list():
            self.add_item(asset)

    def select_by_name(self, name: str):
        """Select a list item by asset name."""
        index = self._getIndex(name)
        self.setCurrentRow(index)

    def _iterAllItems(self) -> RichListItem:  # pylint: disable=invalid-name
        for i in range(self.count()):
            yield self.item(i)

    def _getIndex(self, wanted_item: str) -> int:  # pylint: disable=invalid-name
        """Helper method to get the index of a specific item."""
        for i, item in enumerate(self._iterAllItems()):
            if wanted_item == item.widget.asset.name:
                return i


class AssetKindFilters(QWidget):
    """Widget providing filter checkboxes for given kinds (char, prop...)."""

    def __init__(self, kinds: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signals = Signals()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        show_filters_checkbox = QCheckBox("Show Filters", self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)
        grid_widget.setVisible(False)

        num_cols = 3
        for i, kind in enumerate(kinds):
            row, col = divmod(i, num_cols)
            kind_checkbox = QCheckBox(kind, self)
            kind_checkbox.toggled.connect(
                partial(self.signals.filter_changed.emit, kind)
            )
            grid_layout.addWidget(kind_checkbox, row, col)

        show_filters_checkbox.toggled.connect(grid_widget.setVisible)

        vbox.addWidget(show_filters_checkbox)
        vbox.addWidget(grid_widget)

        self.setLayout(vbox)


class SearchableFilteredAssetList(QWidget):
    """Widget with search field and (filtered) asset list."""

    def __init__(self, asset_provider: AssetProvider, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signals = Signals()
        self.asset_provider = asset_provider

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 5, 0, 0)
        search_line = QLineEdit()
        self.asset_list = AssetList(self.asset_provider)
        self.asset_list.itemSelectionChanged.connect(self._asset_selected)
        kinds = self.asset_provider.flow_provider.kinds
        if kinds:
            asset_kind_filter = AssetKindFilters(kinds)
            asset_kind_filter.signals.filter_changed.connect(
                self.asset_list.change_filter
            )
        search_line.textChanged.connect(self.asset_list.change_search_text)

        headline_hbox = QHBoxLayout()
        headline_hbox.setContentsMargins(0, 0, 0, 0)
        headline = QLabel("Assets")
        headline.setMinimumHeight(ui_constants.BROWSER_HEADLINE_HEIGHT)
        headline.setFont(HeadlineFont())
        headline_hbox.addWidget(headline)
        headline_hbox.addStretch()
        reload_button = QPushButton("")
        reload_button.setIcon(QIcon("icons:reload.svg"))
        reload_button.setMaximumHeight(22)
        reload_button.setMaximumWidth(22)
        reload_button.clicked.connect(self.reload)
        headline_hbox.addWidget(reload_button)
        add_asset_button = QPushButton("Create Assets")
        add_asset_button.setMinimumWidth(80)
        add_asset_button.setMaximumWidth(80)
        add_asset_button.clicked.connect(partial(CreateAssetsWindow, asset_provider))
        headline_hbox.addWidget(add_asset_button)
        vbox.addLayout(headline_hbox)
        vbox.addWidget(search_line)
        if kinds:
            vbox.addWidget(asset_kind_filter)
        vbox.addWidget(self.asset_list)
        self.setLayout(vbox)

    def _asset_selected(self):
        selected = self.asset_list.selectedItems()
        if not selected:
            return
        item = selected[0]
        self.signals.asset_selected.emit(item.widget.asset)

    def refresh(self):
        """If asset list changes through UI input."""
        self.asset_list.refresh()

    def reload(self):
        """If asset list changed throug outside influences."""
        selected = self.asset_list.selectedItems()
        if selected:
            selected = selected[0].widget.asset.name
        self.asset_provider.reload()
        self.refresh()
        if selected:
            self.asset_list.select_by_name(selected)