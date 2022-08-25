"""The ui for Asset Browsing"""
import importlib

from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QHLine, QSplitWidget

from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QFont, QIcon, Qt  # pylint:disable=wrong-import-order
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class BrowseWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout()
        layout.addWidget(QPushButton("BROWSE"))
        self.setLayout(layout)


class InWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout()
        layout.addWidget(QPushButton("IN"))
        self.setLayout(layout)


class OutWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout()
        layout.addWidget(QPushButton("OUT"))
        self.setLayout(layout)


@bind_to_host
class AssetBrowser(QMainWindow):
    """The main Capito window."""

    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        
        self.tab_widget = QTabWidget(self)

        tab_index_1 = self.tab_widget.addTab(BrowseWidget(), "BROWSE")
        self.tab_widget.setTabIcon(tab_index_1, QIcon("icons:failed.svg"))
        self.tab_widget.setIconSize(QtCore.QSize(32, 32))

        if host != "system":
            tab_index_2 = self.tab_widget.addTab(InWidget(), "IN")
            self.tab_widget.setTabIcon(tab_index_2, QIcon("icons:in.svg"))
            self.tab_widget.setIconSize(QtCore.QSize(32, 32))

            tab_index_3 = self.tab_widget.addTab(InWidget(), "OUT")
            self.tab_widget.setTabIcon(tab_index_3, QIcon("icons:out.svg"))
            self.tab_widget.setIconSize(QtCore.QSize(32, 32))


        self.setCentralWidget(self.tab_widget)
