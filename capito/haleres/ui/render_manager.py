from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from capito.haleres.settings import Settings
from capito.haleres.renderer import Renderer, RendererProvider
from capito.haleres.job import Job, JobProvider
from capito.haleres.ui.job_list_widgets import JobListWidget
from capito.haleres.ui.job_settings_widgets import SettingsWidget
from capito.haleres.ui.job_logs_widgets import JobLogsWidget
from capito.core.ui.decorators import bind_to_host
from capito.haleres.ui.utils import SIGNALS


class JobTabsWidget(QTabWidget):
    def __init__(self, renderer_provider:RendererProvider):
        super().__init__()
        self.renderer_provider = renderer_provider
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()
    
    def _create_widgets(self):
        self.settings_widget = SettingsWidget(self.renderer_provider)
        self.logs_widget = JobLogsWidget()
        
    def _connect_widgets(self):
        pass

    def _create_layout(self):     
        self.addTab(self.settings_widget, "Settings")
        self.addTab(self.logs_widget, "Logs")
        self.setMinimumWidth(800)


@bind_to_host
class RenderManager(QMainWindow):
    def __init__(self, settings:Settings, host: str=None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("HLRS Render Manager")
        self.setMinimumSize(1400, 800)
        
        self.settings = settings
        self.job_provider = JobProvider(settings)
        self.renderer_provider = RendererProvider(settings)
        
        self._create_actions()

        self._create_widgets()
        self._connect_widgets()
        self._create_toolbars()
        self._create_layout()

    def _create_actions(self):
        self.toggle_cron_action = QAction(self)
        self.toggle_cron_action.setText("&Cron running. Click to stop.")
        self.toggle_cron_action.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
    
    def _create_widgets(self):
        self.split_widget = QSplitter(Qt.Horizontal)
        self.split_widget.setStretchFactor(3, 10)
        self.joblist_widget = JobListWidget(self.settings, self.job_provider)
        self.jobtabs_widget = JobTabsWidget(self.renderer_provider)
    
    def _create_toolbars(self):
        cron_toolbar = self.addToolBar("Cron")
        cron_toolbar.addWidget(QLabel("Cron Status:"))
        cron_toolbar.addAction(self.toggle_cron_action)
        
    def _connect_widgets(self):
        self.toggle_cron_action.triggered.connect(self._toggle_cron)

    def _create_layout(self):
        self.split_widget.addWidget(self.joblist_widget)
        self.split_widget.addWidget(self.jobtabs_widget)
        self.setCentralWidget(self.split_widget)
        self.split_widget.setStretchFactor(0,1)
        self.split_widget.setStretchFactor(1,0)

    def _toggle_cron(self):
        self.toggle_cron_action.setText("&Cron stopped. Click to start")
        self.toggle_cron_action.setIcon(self.style().standardIcon(QStyle.SP_BrowserStop))
