"""The widget for Importing, Referencing"""
from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QHLine, QSplitWidget
from PySide6 import QtCore  # pylint:disable=wrong-import-order
from PySide6.QtGui import QColor, QFont, QIcon, Qt  # pylint:disable=wrong-import-order
from PySide6.QtWidgets import (  # pylint:disable=wrong-import-order
    QAbstractItemView,
    QAction,
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
    QMenu,
    QMenuBar,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabBar,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class InputWidget(QWidget):
    def __init__(self, host, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("IN"))
        self.setLayout(layout)
