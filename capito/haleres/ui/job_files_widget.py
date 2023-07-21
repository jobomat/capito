from pathlib import Path
import shutil

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.core.ui.widgets import IterableListWidget
from capito.haleres.job import Job
from capito.haleres.ui.utils import SIGNALS


class JobScenefilesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.job:Job = None
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

        SIGNALS.job_selected.connect(self.load_job)
    
    def _create_widgets(self):
        self.scenefile_list = IterableListWidget()
        self.scenefile_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.scenefile_list.setMinimumWidth(250)
        self.remove_file_btn = QPushButton("Remove Selected")
        self.add_file_btn = QPushButton("Add File(s)")
        
    def _connect_widgets(self):
        self.add_file_btn.clicked.connect(self._browse_files)
        self.remove_file_btn.clicked.connect(self._remove_files)

    def _create_layout(self):     
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("Scene Files:"))
        vbox.addWidget(self.scenefile_list, stretch=1)

        hbox = QHBoxLayout()
        hbox.addWidget(self.remove_file_btn)
        hbox.addWidget(self.add_file_btn)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def load_job(self, job:Job):
        self.job = job
        self._reload_list()

    def _reload_list(self):
        self.scenefile_list.clear()
        for scenefile in self.job.scene_files:
            self.scenefile_list.addItem(scenefile.name)

    def _browse_files(self):
        files = QFileDialog.getOpenFileNames(
            self,
            "Select one or more files to add",
            self.job.haleres_settings.share_to_letter(self.job.share)
        )
        if files:
            scenes_folder = self.job.get_folder("scenes")
            for file in files[0]:
                from_file = Path(file)
                to_file = scenes_folder / from_file.name
                shutil.copy(from_file, to_file)
            self._reload_list()

    def _remove_files(self):
        selected_items = self.scenefile_list.selectedItems()
        scenes_folder = self.job.get_folder("scenes")
        for item in selected_items:
            self.scenefile_list.takeItem(self.scenefile_list.row(item))
            file = scenes_folder / item.text()
            print(f"Deleting {file.name} from scenes folder.")
            file.unlink()
        self._reload_list()


class LinkedFilesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.job:Job = None
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

        SIGNALS.job_selected.connect(self.load_job)
    
    def _create_widgets(self):
        self.linkedfile_list = IterableListWidget()
        self.linkedfile_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.linkedfile_list.setMinimumWidth(250)
        self.remove_file_btn = QPushButton("Remove Selected")
        self.add_file_btn = QPushButton("Add File(s)")
        
    def _connect_widgets(self):
        self.add_file_btn.clicked.connect(self._browse_files)
        self.remove_file_btn.clicked.connect(self._remove_files)

    def _create_layout(self):     
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("Linked Files:"))
        vbox.addWidget(self.linkedfile_list, stretch=1)

        hbox = QHBoxLayout()
        hbox.addWidget(self.remove_file_btn)
        hbox.addWidget(self.add_file_btn)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def load_job(self, job:Job):
        self.job = job
        self._reload_list()

    def _reload_list(self):
        self.linkedfile_list.clear()
        for linked_file in self.job.linked_files:
            self.linkedfile_list.addItem(linked_file)

    def _browse_files(self):
        files = QFileDialog.getOpenFileNames(
            self,
            "Select one or more files to add",
            self.job.haleres_settings.share_to_letter(self.job.share)
        )
        if files:
            self.job.linked_files += files[0]
            self._reload_list()

    def _remove_files(self):
        selected_items = self.linkedfile_list.selectedItems()
        scenes_folder = self.job.get_folder("scenes")
        for item in selected_items:
            self.linkedfile_list.takeItem(self.linkedfile_list.row(item))
        self.job.linked_files = [item.text() for item in self.linkedfile_list.iterAllItems()]
        self._reload_list()