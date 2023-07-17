from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.haleres.settings import Settings
from capito.haleres.renderer import Renderer, RendererProvider
from capito.haleres.job import Job, JobProvider
from capito.haleres.ui.joblist_widgets import JobListWidget
from capito.core.ui.decorators import bind_to_host


@bind_to_host
class TestWindow(QMainWindow):
    def __init__(self, settings:Settings, host: str=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.job_provider = JobProvider(settings)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.setWindowTitle("TEST")
        vbox = QVBoxLayout()
        self.joblist_widget = JobListWidget(self.settings)
        vbox.addWidget(self.joblist_widget)
        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

        self.load_all_jobs()

    def load_all_jobs(self):
        for job in self.job_provider.jobs:
            self.joblist_widget.add_job(job)