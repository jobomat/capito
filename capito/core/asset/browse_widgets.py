"""The widget for Asset Browsing"""
import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import List

from capito.core.asset.models import Asset
from capito.core.asset.providers.baseclass import AssetProvider
from capito.core.asset.providers.mock import MockAssetProvider
from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QHLine, QSplitWidget
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QFont  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QIcon, QPixmap, Qt
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QAbstractItemView,
    QAction,
    QCheckBox,
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

CAPITO_ICONS_PATH = Path(os.environ["CAPITO_BASE_DIR"]) / "resources" / "icons"


class Signals(QtCore.QObject):
    """Special Signals for communicating between custom Widgets"""

    filter_changed = QtCore.Signal(str, bool)

    def __init__(self):
        super().__init__()


class VersionItemWidget(QWidget):
    """Presentation Widget for a single Item in the Version List."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(5, 5, 5, 5)

        left_vbox = QVBoxLayout()
        version_label = QLabel("0001")
        version_label_font = QFont()
        version_label_font.setBold(True)
        version_label_font.setPointSize(12)
        version_label.setFont(version_label_font)
        #        thumb_pixmap = QPixmap.fromImage(
        thumb_pixmap = QPixmap(str(CAPITO_ICONS_PATH / "char.png")).scaled(
            80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        thumb_label = QLabel()
        thumb_label.setPixmap(thumb_pixmap)
        left_vbox.addWidget(version_label)
        left_vbox.addWidget(thumb_label)
        hbox.addLayout(left_vbox)

        right_vbox = QVBoxLayout()
        date_user_hbox = QHBoxLayout()
        date_label = QLabel("24.12.22 | 12:15")
        user_label = QLabel("jobo")
        date_user_hbox.addWidget(date_label)
        date_user_hbox.addStretch()
        date_user_hbox.addWidget(user_label)
        right_vbox.addLayout(date_user_hbox)
        comment_label = QLabel(
            "A QPixmap can be used to show an image in a PyQT window."
        )
        comment_label.setWordWrap(True)
        right_vbox.addStretch()
        right_vbox.addWidget(comment_label)
        hbox.addLayout(right_vbox)

        self.setLayout(hbox)


class RichListItem(QListWidgetItem):
    """A QListWidgetItem that uses whatever widget is handed for Presentation."""

    def __init__(self, widget: QWidget, parent):
        super().__init__(parent)
        self.widget = widget
        self.setSizeHint(self.widget.minimumSizeHint())
        parent.setItemWidget(self, self.widget)


class BrowseToolbar(QWidget):
    """The upper toolbar"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        create_button = QPushButton("Create Asset(s)")
        hbox.addWidget(create_button)
        hbox.addStretch()

        self.setLayout(hbox)


class AssetItemWidget(QWidget):
    """Presentation Widget for a single Item in the Asset List."""

    def __init__(self, asset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset = asset
        vbox = QVBoxLayout()
        vbox.setContentsMargins(5, 2, 0, 2)

        hbox = QHBoxLayout()
        asset_label = QLabel(asset.name)
        asset_label_font = QFont()
        asset_label_font.setBold(True)
        asset_label_font.setPointSize(14)
        asset_label.setFont(asset_label_font)
        thumb_pixmap = QPixmap(str(CAPITO_ICONS_PATH / f"{asset.kind}.svg")).scaled(
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

    def __init__(self, asset_provider:AssetProvider, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QListWidget.EditKeyPressed)
        self.asset_provider = asset_provider
        self.search_text = ""
        self.kind_filters = []
        for asset in asset_provider.list():
            self.add_item(asset)

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
            if self.search_text in item.widget.asset.name and (not self.kind_filters or item.widget.asset.kind in self.kind_filters):
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
        

class AssetKindFilters(QWidget):
    """Widget providing filter checkboxes for given kinds (char, prop...)."""
    def __init__(self,kinds:List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signals = Signals()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        show_filters_checkbox = QCheckBox("Show Filters", self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)
        grid_widget.setVisible(False)
        
        num_cols = 4
        for i, kind in enumerate(kinds):
            row, col = divmod(i, num_cols)
            kind_checkbox = QCheckBox(kind, self)
            kind_checkbox.toggled.connect(partial(self.signals.filter_changed.emit, kind))
            grid_layout.addWidget(kind_checkbox, row, col)
        
        show_filters_checkbox.toggled.connect(grid_widget.setVisible)

        vbox.addWidget(show_filters_checkbox)
        vbox.addWidget(grid_widget)

        self.setLayout(vbox)


class SearchableAssetList(QWidget):
    """Widget with search field and (filtered) asset list."""

    def __init__(self, asset_provider, *args, **kwargs):
        super().__init__(*args, **kwargs)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        search_line = QLineEdit()
        asset_list = AssetList(asset_provider)
        search_line.textChanged.connect(asset_list.change_search_text)
        vbox.addWidget(search_line)
        vbox.addWidget(asset_list)
        self.setLayout(vbox)


class SearchableFilteredAssetList(QWidget):
    """Widget with search field and (filtered) asset list."""

    def __init__(self, asset_provider: AssetProvider, kinds:List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        search_line = QLineEdit()
        asset_list = AssetList(asset_provider)
        asset_kind_filter = AssetKindFilters(kinds)
        search_line.textChanged.connect(asset_list.change_search_text)
        asset_kind_filter.signals.filter_changed.connect(asset_list.change_filter)
        vbox.addWidget(search_line)
        vbox.addWidget(asset_kind_filter)
        vbox.addWidget(asset_list)
        self.setLayout(vbox)


class BrowseWidget(QWidget):
    """The top widget for the BROWSE tab."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        vbox = QVBoxLayout()
        self.browse_toolbar = BrowseToolbar()
        vbox.addWidget(self.browse_toolbar)

        vsplitter = QSplitter(Qt.Horizontal)

        asset_provider = MockAssetProvider()

        asset_list = SearchableFilteredAssetList(asset_provider, ["char", "prop", "set", "seq", "shot", "gen"])
        vsplitter.addWidget(asset_list)

        version_list = QListWidget()
        version_list.addItem(RichListItem(VersionItemWidget(), version_list))
        version_list.addItem(RichListItem(VersionItemWidget(), version_list))
        version_list.addItem(RichListItem(VersionItemWidget(), version_list))
        version_list.setStyleSheet(
            """
            QListWidget::item {background-color:#363636; margin-bottom: 3px;}
            QListWidget::item:hover {background-color:#666666}
            QListWidget::item:selected {background-color:#555555}
            """
        )
        vsplitter.addWidget(version_list)
        right = QFrame()
        right.setFrameShape(QFrame.Panel)
        vsplitter.addWidget(right)

        vbox.addWidget(vsplitter, stretch=1)

        self.setLayout(vbox)
