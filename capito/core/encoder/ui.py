import os
from pathlib import Path

from plumbum import local
from plumbum.commands.processes import CommandNotFound
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QFont, QIcon, Qt  # pylint:disable=wrong-import-order
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from capito.core.ui.decorators import bind_to_host
import capito.core.encoder.widgets as encoder_widgets 

ffmpeg_path = os.environ.get("FFMPEG", "ffmpeg") #path or "ffmpeg"
try:
    ffmpeg = local[ffmpeg_path]
except CommandNotFound:
    ffmpeg = None


@bind_to_host
class SequenceEncoderUI(QMainWindow):
    """The main manager window."""

    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sequence Encoder")
        self.setMinimumSize(500, 500)

        vbox = QVBoxLayout()
        
        if ffmpeg is not None:
            main_widget = encoder_widgets.MainWidget(ffmpeg)
        else:
            main_widget = encoder_widgets.ErrorWidget()
        vbox.addWidget(main_widget)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)