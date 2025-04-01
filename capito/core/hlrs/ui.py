import os
from pathlib import Path

from PySide6 import QtCore  # pylint:disable=wrong-import-order
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QColor, QFont, QIcon, Qt  # pylint:disable=wrong-import-order
from PySide6.QtWidgets import (  # pylint:disable=wrong-import-order
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from capito.core.ui.decorators import bind_to_host
import capito.core.hlrs.widgets as hlrs_widgets



@bind_to_host
class HLRSConnectorUI(QMainWindow):
    """The main manager window."""

    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)

        self.setWindowTitle("HLRS")
        self.setMinimumSize(1024, 640)

        vbox = QVBoxLayout()
        
        main_widget = hlrs_widgets.MainWidget(self)
        
        vbox.addWidget(main_widget)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)
