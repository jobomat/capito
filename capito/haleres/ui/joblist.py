from functools import partial

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.core.ui.widgets import IterableListWidget, RichListItem
from capito.haleres.job import Job


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

        self.push_progressbar = QProgressBar(maximum=job.get_push_max(), objectName="PushProgressBar")
        self.push_progressbar.setFixedWidth(50)
        self.submit_progressbar = QProgressBar(maximum=job.num_jobs(), objectName="SubmitProgressBar")
        self.submit_progressbar.setFormat("%v/%m")
        self.submit_progressbar.setFixedWidth(50)
        self.render_progressbar = QProgressBar(maximum=job.num_expected_renders(), objectName="RenderProgressBar")
        self.render_progressbar.setFormat("%v/%m")
        self.render_progressbar.setFixedWidth(50)
        self.pull_progressbar = QProgressBar(maximum=job.num_expected_pulls(), objectName="PullProgressBar")
        self.pull_progressbar.setFormat("%v/%m")
        self.pull_progressbar.setFixedWidth(50)

        hbox.addWidget(QLabel(f"{job.name}"), stretch=1)
        hbox.addWidget(QLabel(f"{job.share}  "))
        hbox.addWidget(self.push_progressbar)
        hbox.addWidget(self.submit_progressbar)
        hbox.addWidget(self.render_progressbar)
        hbox.addWidget(self.pull_progressbar)
        self.setLayout(hbox)
    
    def update(self):
        if self.job.is_finished():
            return
        self.force_update()
        
    def force_update(self):
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

        refresh_interval = 4000
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(refresh_interval)

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

    def __init__(self):
        super().__init__()

        vbox = QVBoxLayout()
        self.filters = JobFilterWidget()
        self.job_list = JobList()

        self.filters.filter_changed.connect(self.job_list.filter)

        vbox.addWidget(self.filters)
        vbox.addWidget(JobListHeaderWidget())
        vbox.addWidget(self.job_list)

        self.setLayout(vbox)

    def add_job(self, job):
        self.job_list.add_job(job)
        self.filters.emit_filter_changed()