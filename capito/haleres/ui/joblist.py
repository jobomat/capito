from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.haleres.job import Job


class ProgressBarDelegate(QStyledItemDelegate):
    def __init__(self, column, parent=None):
        super().__init__(parent)
        self.column = column

    def paint(self, painter, option, index):
        if index.column() == self.column:  # Assuming the progress bar should be displayed in the second column
            job_dict = index.data(Qt.DisplayRole)
            progress = job_dict["progress_function"]()
            if isinstance(progress, int):
                progressBarOption = QStyleOptionProgressBar()
                progressBarOption.rect = option.rect
                progressBarOption.minimum = 0
                progressBarOption.maximum = job_dict["max"]
                progressBarOption.progress = progress
                progressBarOption.textVisible = True
                progressBarOption.textAlignment = Qt.AlignCenter
                progressBarOption.text = f"{progress}/{job_dict['max']}"

                font = painter.font()
                font.setPointSize(7)
                painter.setFont(font)

                progressBar = QProgressBar(option.widget)
                progressBar.setValue(progress)
                
                progressBarStyle = QApplication.style()
                progressBarStyle.drawControl(QStyle.CE_ProgressBar, progressBarOption, painter, progressBar)

    def sizeHint(self, option, index):
        return super().sizeHint(option, index)
    

class JobListProgressItem(QStandardItem):
    def __init__(self, job, max_progress, progress_function):
        super().__init__()
        self.job = job
        self.max_progress = max_progress
        self.progress_function = progress_function
        self.update_progress()

    def update_progress(self):
        self.setData(
            {
                "job": self.job, "max": self.max_progress,
                "progress_function":getattr(self.job, self.progress_function)
            },
            Qt.DisplayRole
        )


class JobList(QTreeView):
    def __init__(self):
        super().__init__()
        self.jobs = []

        self.header_labels = ["Name", "Push", "Subm", "Rend", "Pull"]
        self.num_cols = len(self.header_labels)
        self._model = QStandardItemModel(0, self.num_cols)
        self._model.setHorizontalHeaderLabels(self.header_labels)
        self.setModel(self._model)

        self.push_delegate = ProgressBarDelegate(1)
        self.setItemDelegateForColumn(1, self.push_delegate)
        self.submit_delegate = ProgressBarDelegate(2)
        self.setItemDelegateForColumn(2, self.submit_delegate)
        self.render_delegate = ProgressBarDelegate(3)
        self.setItemDelegateForColumn(3, self.render_delegate)
        self.pull_delegate = ProgressBarDelegate(4)
        self.setItemDelegateForColumn(4, self.pull_delegate)

        for i in range(1, self.num_cols +1):
            self.setColumnWidth(i, 50)

        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setStretchLastSection(False)

        refresh_interval = 5000
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(refresh_interval)

    def add_job(self, job:Job):
        self.jobs.append(job)
        row = self._model.rowCount()
        self._model.setItem(row, 0, QStandardItem(job.name))
        
        push_item = JobListProgressItem(job, job.get_push_max(), "get_push_progress")
        self._model.setItem(row, 1, push_item)
        submit_item = JobListProgressItem(job, job.get_submit_max(), "get_submit_progress")
        self._model.setItem(row, 2, submit_item)
        render_item = JobListProgressItem(job, job.get_render_max(), "get_render_progress")
        self._model.setItem(row, 3, render_item)
        pull_item = JobListProgressItem(job, job.get_pull_max(), "get_pull_progress")
        self._model.setItem(row, 4, pull_item)

        self.update_progress()

    def update_progress(self):
        for row in range(self._model.rowCount()):
            for i in range(1, self.num_cols):
                self._model.item(row, i).update_progress()