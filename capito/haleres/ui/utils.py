from typing import List

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.haleres.job import Job
from capito.haleres.renderer import Renderer


class SignalManager(QObject):
    job_selected = Signal(Job)
    joblist_updated = Signal(List[Job])
    renderer_selected = Signal(Renderer)
    save_job_settings_clicked = Signal(Job)


SIGNALS = SignalManager()


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
            child.widget().setParent(None)