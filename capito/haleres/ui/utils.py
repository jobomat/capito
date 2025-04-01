from typing import List
from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from capito.haleres.job import Job
from capito.haleres.renderer import Renderer


class SignalManager(QObject):
    job_selected = Signal(Job)
    renderer_selected = Signal(Renderer)
    save_job_settings_clicked = Signal(Job)
    log_file_selected = Signal(Path)


SIGNALS = SignalManager()


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
            child.widget().setParent(None)