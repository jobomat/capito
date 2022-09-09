import os
from pathlib import Path

from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtCore import Signal, QObject
from PySide2.QtGui import QColor, QFont, QIcon, Qt  # pylint:disable=wrong-import-order
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from capito.core.ui.decorators import bind_to_host
import capito.core.encoder.widgets as encoder_widgets
from capito.core.encoder.encoder import SequenceEncoder


class Signals(QObject):
    closed = Signal()
    def __init__(self):
        super().__init__()


@bind_to_host
class SequenceEncoderUI(QMainWindow):
    """The main manager window."""

    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)

        self.encoder = SequenceEncoder()

        self.signals = Signals()
        self.setWindowTitle("Sequence Encoder")
        self.setMinimumSize(640, 500)

        vbox = QVBoxLayout()
        
        if self.encoder.is_ready():
            main_widget = encoder_widgets.MainWidget(self)
        else:
            main_widget = encoder_widgets.ErrorWidget()
        vbox.addWidget(main_widget)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def closeEvent(self, event):
        self.signals.closed.emit()
        super().closeEvent(event)

