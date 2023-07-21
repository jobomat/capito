from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.haleres.job import Job


class JobLogsWidget(QWidget):
    def __init__(self):
        super().__init__()