from functools import partial
from pathlib import Path
from typing import Callable

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.core.ui.widgets import IterableListWidget, RichListItem
from capito.haleres.job import Job, JobProvider
from capito.haleres.settings import Settings
from capito.core.ui.decorators import bind_to_host
from capito.haleres.ui.utils import SIGNALS


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
        background-color: rgb(255, 152, 51);
    }
    #SubmitProgressBar::chunk {
        background-color: rgb(40, 170, 0);
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
    def __init__(self, add_job_callback:Callable, settings, preselected_share="cg1", parent=None, host=None):
        super().__init__(parent)
        self.add_job_callback = add_job_callback
        self.share = preselected_share
        self.settings = settings
        self.setWindowTitle("Create new Job")

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Share: "))

        shares = [share for share, letter in settings.share_map.items() if (Path(letter)/"hlrs").exists()]
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
            #print(f"Starting timer for {self.job.name}")
            self.update_timer.start(self.refresh_interval)
        else:
            #print(f"Stopping timer for {self.job.name}")
            self.update_timer.stop()
    
    def update(self):
        self.force_update()
        #print(f"Executing update for {self.job.name}, is_active: {self.job.is_active()}")
        if not self.job.is_active():
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
        
        self.itemSelectionChanged.connect(self._job_selected)

    def add_job(self, job):
        job_widget = JobListRowWidget(job)
        job_widget.force_update()
        item = RichListItem(job_widget, self)
        self.addItem(item)

    def update_progress(self):
        for item in self.iterAllItems():
            item.widget.update()

    def _job_selected(self):
        try:
            job = self.selectedItems()[0].widget.job
            SIGNALS.job_selected.emit(job)
        except:
            pass
        
    def _context_menu(self, qpoint):
        menu = QMenu(self)
        abort_push_action = QAction("Abort Push")
        abort_push_action.triggered.connect(partial(self._abort_push))
        menu.addAction(abort_push_action)
        pause_action = QAction("Pause/Unpause")
        pause_action.triggered.connect(partial(self._toggle_pause))
        menu.addAction(pause_action)
        abort_job = QAction("Abort Job")
        abort_job.triggered.connect(partial(self._abort_job))
        menu.addAction(abort_job)
        menu.exec_(QCursor.pos())
    
    def _abort_push(self):
        widget = self.selectedItems()[0].widget
        self.parent().abort_push_triggered.emit(widget.job)

    def _toggle_pause(self):
        widget = self.selectedItems()[0].widget
        current_state = not widget.job.is_paused()
        widget.job.set_paused(current_state)
        widget.update_progressbars(not current_state)
        self.parent().pause_triggered.emit(widget.job)

    def _abort_job(self):
        widget = self.selectedItems()[0].widget
        widget.job.set_aborted(True)
        widget.job.set_finished(True)

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

    def __init__(self, settings:Settings, preselected_share:str="All", show_hide_finished:bool=True):
        super().__init__()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(5,1,0,1)
        hbox.setSpacing(1)
        hbox.addWidget(QLabel("Show: "))

        self.share = preselected_share
        shares = [share for share, letter in settings.share_map.items() if (Path(letter)/"hlrs").exists()]
        shares.append(preselected_share)
        for share in shares:
            btn = QRadioButton(share)
            btn.setChecked(share==preselected_share)
            btn.toggled.connect(partial(self.set_share, btn))
            hbox.addWidget(btn)
        
        hbox.addStretch()
        self.show_finished_checkbox = QCheckBox("Hide Finished Jobs")
        self.show_finished_checkbox.stateChanged.connect(self.emit_filter_changed)
        self.show_finished_checkbox.setVisible(show_hide_finished)
        hbox.addWidget(self.show_finished_checkbox)

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

    def __init__(self, settings:Settings, job_provider:JobProvider):
        super().__init__()
        self.job_provider = job_provider

        self.filters = JobFilterWidget(settings)
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

        self.rebuild_joblist()

        self.refresh_interval = 5000
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(self.refresh_interval)

    def update(self):
        if self.job_provider.joblist_changed():
            self.rebuild_joblist()
    
    def rebuild_joblist(self):
        self.job_list.clear()
        for job in self.job_provider.jobs:
            self.add_job(job)

    def add_job(self, job):
        self.job_list.add_job(job)
        self.filters.emit_filter_changed()


class SimpleJobListWidget(QWidget):
    def __init__(self, settings:Settings, preselected_share="All", show_hide_finished=False):
        super().__init__()

        self.filter_widget = JobFilterWidget(settings, preselected_share, show_hide_finished)
        self.joblist_widget = IterableListWidget()

        self.filter_widget.filter_changed.connect(self._filter)

        vbox = QVBoxLayout()
        vbox.addWidget(self.filter_widget)
        vbox.addWidget(self.joblist_widget)
        self.setLayout(vbox)

    def add_job(self, job:Job):
        item = QListWidgetItem()
        item.setText(f"{job.share} | {job.name}")
        item.setData(Qt.UserRole, job)
        self.joblist_widget.addItem(item)

    def get_selected_jobs(self):
        return [item.data(Qt.UserRole) for item in self.joblist_widget.selectedItems()]
    
    def select_job(self, job:Job):
        for item in self.joblist_widget.iterAllItems():
            if item.data(Qt.UserRole) == job:
                self.joblist_widget.setCurrentItem(item)
                break

    def _filter(self, share:str, hide_finished:bool):
        for item in self.joblist_widget.iterAllItems():
            item.setHidden(False)
            job = item.data(Qt.UserRole)
            if share != "All" and job.share != share:
                item.setHidden(True)
                continue
            if hide_finished and job.is_finished():
                item.setHidden(True)



@bind_to_host
class ChooseJobWin(QMainWindow):
    def __init__(self, settings:Settings, on_select_clicked:Callable,
                 enable_job_creation:bool=True, preselected_share="All",
                 parent=None, host=None):
        super().__init__(parent)
        self.share = preselected_share
        self.settings = settings
        self.callback = on_select_clicked

        self.job_provider = JobProvider(settings)
        self.setWindowTitle("Choose Job")

        self.job_list_widget = SimpleJobListWidget(settings, preselected_share)
        create_job_btn = QPushButton("Create Job")
        select_job_btn = QPushButton("Select Job")

        hbox = QHBoxLayout()
        if enable_job_creation:
            hbox.addWidget(create_job_btn)
        hbox.addWidget(select_job_btn)

        create_job_btn.clicked.connect(self._create_job_clicked)
        select_job_btn.clicked.connect(self._selected_clicked)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.job_list_widget)
        vbox.addLayout(hbox)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

        for job in self.job_provider.jobs:
            self.job_list_widget.add_job(job)

    def _selected_clicked(self):
        jobs = self.job_list_widget.get_selected_jobs()
        if not jobs:
            return
        self.callback(jobs[0])
        self.close()

    def _create_job_clicked(self):
        CreateJobWin(self._add_job, self.settings)

    def _add_job(self, job):
        self.job_list_widget.add_job(job)
        self.job_list_widget.select_job(job)
