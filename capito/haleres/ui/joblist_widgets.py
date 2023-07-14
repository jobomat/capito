from functools import partial
from typing import Callable

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.core.ui.widgets import IterableListWidget, RichListItem
from capito.haleres.job import Job
from capito.core.ui.decorators import bind_to_host


JOBLIST_STYLESHEET = '''
    #JobRow {
        border: 1px solid;
        border-color: #000000;
    }
    #PushProgressBar, #SubmitProgressBar, #RenderProgressBar, #PullProgressBar {
        text-align: center;
        padding: 0 px;
        margin: 0 px;
    }
    #PushProgressBar::chunk {
        background-color: rgb(255, 180, 0);
    }
    #SubmitProgressBar::chunk {
        background-color: rgb(255, 152, 51);
    }
    #RenderProgressBar::chunk {
        background-color: rgb(0, 127, 255);
    }
    #PullProgressBar::chunk {
        background-color: rgb(204, 0, 204);
    }
'''

@bind_to_host
class CreateJobWin(QMainWindow):
    def __init__(self, add_job_callback:Callable, settings, shares=["cg1", "cg2", "cg3"],
                 preselected_share="cg1", parent=None, host=None):
        super().__init__(parent)
        self.add_job_callback = add_job_callback
        self.share = preselected_share
        self.settings = settings
        self.setWindowTitle("Create new Job")

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Share: "))
        for share in shares:
            btn = QRadioButton(share)
            btn.setChecked(share==self.share)
            btn.toggled.connect(partial(self._set_share, btn))
            hbox.addWidget(btn)
        self.name_lineedit = QLineEdit()
        vbox.addLayout(hbox)
        vbox.addWidget(self.name_lineedit)
        add_btn = QPushButton("Create Job")
        add_btn.clicked.connect(self.add_job)
        vbox.addWidget(add_btn)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def _set_share(self, share_btn, value):
        self.share = share_btn.text()

    def add_job(self):
        """Call the callback function and pass the job."""
        name = self.name_lineedit.text()
        if not name:
            return
        job = Job(self.share, name, self.settings)
        job.create_job_folders()
        self.add_job_callback(job)
        self.close()



class JobListHeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(5,1,0,1)
        hbox.setSpacing(1)
        hbox.addWidget(QLabel("Job name"), stretch=1)
        hbox.addWidget(QLabel("Share  "))
        for label in ["Push", "Submit", "Render", "Pull"]:
            label = QLabel(label)
            label.setFixedWidth(50)
            hbox.addWidget(label)
        self.setLayout(hbox)


class JobListRowWidget(QWidget):
    def __init__(self, job:Job, parent=None):
        super().__init__(parent)
        self.job = job
        hbox = QHBoxLayout(objectName="JobRow")
        hbox.setContentsMargins(5,1,0,1)
        hbox.setSpacing(1)

        self.push_progressbar = QProgressBar(maximum=1, objectName="PushProgressBar")
        self.push_progressbar.setFixedWidth(50)
        self.submit_progressbar = QProgressBar(maximum=1, objectName="SubmitProgressBar")
        self.submit_progressbar.setFormat("...")
        self.submit_progressbar.setFixedWidth(50)
        self.render_progressbar = QProgressBar(maximum=1, objectName="RenderProgressBar")
        self.render_progressbar.setFormat("...")
        self.render_progressbar.setFixedWidth(50)
        self.pull_progressbar = QProgressBar(maximum=1, objectName="PullProgressBar")
        self.pull_progressbar.setFormat("...")
        self.pull_progressbar.setFixedWidth(50)

        hbox.addWidget(QLabel(f"{job.name}"), stretch=1)
        hbox.addWidget(QLabel(f"{job.share}  "))
        hbox.addWidget(self.push_progressbar)
        hbox.addWidget(self.submit_progressbar)
        hbox.addWidget(self.render_progressbar)
        hbox.addWidget(self.pull_progressbar)
        self.setLayout(hbox)
        
        self.refresh_interval = 5000
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_progressbars(True)


    def update_progressbars(self, update:bool):
        if update:
            print(f"Starting timer for {self.job.name}")
            self.update_timer.start(self.refresh_interval)
        else:
            print(f"Stopping timer for {self.job.name}")
            self.update_timer.stop()
    
    def update(self):
        self.force_update()
        print(f"Executing update for {self.job.name}")
        if self.job.is_active():
            self.update_progressbars(False)
        
    def force_update(self):
        push_max = self.job.get_push_max()
        num_jobs = self.job.num_jobs()
        num_expected_renders = self.job.num_expected_renders()
        num_expected_pulls = self.job.num_expected_pulls()
    
        self.push_progressbar.setMaximum(push_max or 1)
        self.submit_progressbar.setMaximum(num_jobs or 1)
        self.render_progressbar.setMaximum(num_expected_renders or 1)
        self.pull_progressbar.setMaximum(num_expected_pulls or 1)

        if self.job.all_files_pushed():
            self.submit_progressbar.setFormat("%v/%m")
            self.render_progressbar.setFormat("%v/%m")
            self.pull_progressbar.setFormat("%v/%m")

        self.push_progressbar.setValue(self.job.get_push_progress())
        self.submit_progressbar.setValue(self.job.num_submitted_jobs())
        self.render_progressbar.setValue(self.job.num_rendered())
        self.pull_progressbar.setValue(self.job.num_pulled())


class JobList(IterableListWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(JOBLIST_STYLESHEET)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(partial(self._context_menu))

    def add_job(self, job):
        job_widget = JobListRowWidget(job)
        job_widget.force_update()
        item = RichListItem(job_widget, self)
        self.addItem(item)

    def update_progress(self):
        for item in self.iterAllItems():
            item.widget.update()
        
    def _context_menu(self, qpoint):
        menu = QMenu(self)
        abort_push_action = QAction("Abort Push")
        abort_push_action.triggered.connect(partial(self._abort_push))
        menu.addAction(abort_push_action)
        pause_action = QAction("Pause")
        pause_action.triggered.connect(partial(self._pause))
        menu.addAction(pause_action)
        menu.exec_(QCursor.pos())
    
    def _abort_push(self):
        self.parent().abort_push_triggered.emit(self.selectedItems()[0].widget.job)

    def _pause(self):
        self.parent().pause_triggered.emit(self.selectedItems()[0].widget.job)

    def filter(self, share:str, hide_finished:bool):
        for row in self.iterAllItems():
            row.setHidden(False)
            if share != "All" and row.widget.job.share != share:
                row.setHidden(True)
                continue
            if hide_finished and row.widget.job.is_finished():
                row.setHidden(True)


class JobFilterWidget(QWidget):
    filter_changed = Signal(str, bool)

    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(5,1,0,1)
        hbox.setSpacing(1)
        hbox.addWidget(QLabel("Show: "))

        self.share = "All"
        for share in ["All", "cg1", "cg2", "cg3"]:
            btn = QRadioButton(share)
            btn.setChecked(share=="All")
            btn.toggled.connect(partial(self.set_share, btn))
            hbox.addWidget(btn)
        
        hbox.addWidget(QLabel("  "))
        self.show_finished_checkbox = QCheckBox("Hide Finished Jobs")
        self.show_finished_checkbox.stateChanged.connect(self.emit_filter_changed)
        hbox.addWidget(self.show_finished_checkbox)

        hbox.addStretch()
        self.setLayout(hbox)

    def set_share(self, share_btn, value):
        if value:
            self.share = share_btn.text()
            self.emit_filter_changed()

    def emit_filter_changed(self):
        self.filter_changed.emit(self.share, self.show_finished_checkbox.isChecked())
    

class JobListWidget(QWidget):
    abort_push_triggered = Signal(Job)
    pause_triggered = Signal(Job)

    def __init__(self, settings):
        super().__init__()

        self.filters = JobFilterWidget()
        self.job_list = JobList()
        add_btn = QPushButton("Create Job")

        add_btn.clicked.connect(partial(CreateJobWin, self.add_job, settings))
        self.filters.filter_changed.connect(self.job_list.filter)

        vbox = QVBoxLayout()
        vbox.addWidget(self.filters)
        vbox.addWidget(JobListHeaderWidget())
        vbox.addWidget(self.job_list)
        vbox.addWidget(add_btn)

        self.setLayout(vbox)

    def add_job(self, job):
        self.job_list.add_job(job)
        self.filters.emit_filter_changed()


from pathlib import Path
from typing import List

from capito.haleres.renderer import Renderer, RendererProvider
from capito.haleres.settings import Settings
from capito.haleres.job import Job, JobStatus

@bind_to_host
class TestWindow(QMainWindow):
    def __init__(self,  host: str=None, parent=None):
        super().__init__(parent)
        self.settings = Settings("K:/pipeline/hlrs/settings.json")
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
        jobs = []
        for letter, share in self.settings.letter_map.items():
            hlrs_folder = list(Path(letter).glob("hlrs"))
            if hlrs_folder:
                j = [Job(share, name.name, self.settings) for name in hlrs_folder[0].glob("*")]
                jobs.extend(j)
        for job in jobs:
            self.joblist_widget.add_job(job)
