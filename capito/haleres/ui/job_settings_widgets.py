from functools import partial

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.core.ui.widgets import QHLine, IterableListWidget
from capito.haleres.job import Job
from capito.haleres.renderer import Renderer, RendererProvider
from capito.haleres.ui.job_files_widget import JobScenefilesWidget, LinkedFilesWidget
from capito.haleres.ui.renderer_flag_widgets import RendererFlagDisplayList, INT_OR_EMPTY_VALIDATOR
from capito.haleres.ui.utils import SIGNALS


class JobSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.job = None
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()
        self.setMaximumHeight(150)

        SIGNALS.job_selected.connect(self.load_job)
    
    def _create_widgets(self):
        self.framelist_widget = QTextEdit()
        self.framelist_widget.setMaximumHeight(52)
        self.walltime_widget = QLineEdit()
        self.walltime_widget.setValidator(INT_OR_EMPTY_VALIDATOR)
        self.jobsize_widget = QLineEdit()
        self.jobsize_widget.setValidator(INT_OR_EMPTY_VALIDATOR)
        
    def _connect_widgets(self):
        self.framelist_widget.textChanged.connect(self._set_framelist)
        self.walltime_widget.textEdited.connect(self._set_walltime)
        self.jobsize_widget.textEdited.connect(self._set_jobsize)

    def _create_layout(self):     
        grid = QGridLayout()
        grid.setContentsMargins(0,0,0,0)
        grid.addWidget(QLabel("Framelist"), 1, 1, 1, 1, Qt.AlignTop)
        grid.addWidget(self.framelist_widget, 1, 2)
        grid.addWidget(QLabel("Walltime"), 2, 1)
        grid.addWidget(self.walltime_widget, 2, 2)
        grid.addWidget(QLabel("Jobsize"), 3, 1)
        grid.addWidget(self.jobsize_widget, 3, 2)

        self.setLayout(grid)

    def _set_framelist(self):
        if self.job:
            self.job.framelist = self.framelist_widget.toPlainText()
    
    def _set_walltime(self, value:str):
        if self.job and value:
            self.job.walltime_minutes = int(value)
    
    def _set_jobsize(self, value:str):
        if self.job and value:
            self.job.jobsize = int(value)

    def load_job(self, job:Job):
        self.job = job
        blocker = QSignalBlocker(self.framelist_widget)
        self.framelist_widget.setText(job.framelist)
        blocker.unblock()
        self.walltime_widget.setText(str(job.walltime_minutes))
        self.jobsize_widget.setText(str(job.jobsize))




class JobLinkedfilesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()
    
    def _create_widgets(self):
        pass
        
    def _connect_widgets(self):
        pass

    def _create_layout(self):     
        pass


class JobAndRendererSettingsWidget(QWidget):
    def __init__(self, renderer_provider:RendererProvider):
        super().__init__()
        self.job:Job = None
        self.renderer_provider = renderer_provider
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

        SIGNALS.job_selected.connect(self.load_job)
    
    def load_job(self, job:Job):
        self.job = job
        self.renderer_settings_widget.clear_layout()
        self.renderer_combo.setCurrentText("")
        if job.renderer:
            self.renderer_settings_widget.load_flags(job.renderer.get_editable_flags())
            self.renderer_combo.setCurrentText(job.renderer.name)

    def _create_widgets(self):
        self.job_settings_widget = JobSettingsWidget()
        self.renderer_combo = QComboBox()
        self.renderer_combo.addItem("")
        for renderer in self.renderer_provider.renderers:
            self.renderer_combo.addItem(renderer)
        self.renderer_settings_widget = RendererFlagDisplayList()
        self.scroll_widget = QScrollArea()
        #self.scroll_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_widget.setWidgetResizable(True)
        self.scroll_widget.setWidget(self.renderer_settings_widget)
        
    def _connect_widgets(self):
        self.renderer_combo.activated.connect(self._renderer_selected)

    def _create_layout(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.job_settings_widget)
        vbox.addWidget(QHLine())
        vbox.addWidget(QLabel("Renderer and Renderer Overrides:"))
        vbox.addWidget(self.renderer_combo)
        vbox.addWidget(self.scroll_widget, stretch=1)
        self.setLayout(vbox)

    def _renderer_selected(self, index):
        renderer_name = self.renderer_combo.currentText()
        renderer = None
        if renderer_name:
            renderer = self.renderer_provider.renderers[renderer_name]
            self.job.renderer = renderer
            self.job.save_renderer_config()
        SIGNALS.renderer_selected.emit(renderer)

class SettingsWidget(QWidget):
    def __init__(self, renderer_provider:RendererProvider):
        super().__init__()
        self.job:Job = None
        self.renderer_provider = renderer_provider
        
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

        SIGNALS.job_selected.connect(self.load_job)

    def load_job(self, job:Job):
        self.job = job
        self.submit_job_btn.setEnabled(not job.is_ready_to_push())
            
    def _create_widgets(self):
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setHandleWidth(15)
        self.job_and_renderer_settings_widget = JobAndRendererSettingsWidget(self.renderer_provider)
        self.job_and_renderer_settings_widget.setMinimumWidth(220)
        self.scene_list_widget = JobScenefilesWidget()
        self.linked_files_widget = LinkedFilesWidget()
        self.submit_job_btn = QPushButton("Submit")
        self.submit_job_btn.setEnabled(False)
    
    def _connect_widgets(self):
        self.submit_job_btn.clicked.connect(self._save_clicked)

    def _create_layout(self):
        vbox = QVBoxLayout()
        #vbox.setContentsMargins(0,0,0,0)

        self.splitter.addWidget(self.job_and_renderer_settings_widget)
        self.splitter.addWidget(self.scene_list_widget)
        self.splitter.addWidget(self.linked_files_widget)

        buttons_hbox = QHBoxLayout()
        buttons_hbox.addStretch()
        buttons_hbox.addWidget(self.submit_job_btn)

        vbox.addWidget(self.splitter, stretch=1)
        vbox.addLayout(buttons_hbox)
        self.setLayout(vbox)

    def _save_clicked(self):
        self.job.write_job_files()
        self.job.create_rsync_push_file()
        self.job.set_ready_to_push(True)
        print("TODO: Check job settings, render config, scenes and linked files")