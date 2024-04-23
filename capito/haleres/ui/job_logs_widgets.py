from pathlib import Path

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.haleres.job import Job
from capito.haleres.ui.utils import SIGNALS


class LogSelectionWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.job = None

        self.log_dirs_dict = {
            "Renderer Logs": Job.job_folders["logs"],
            "Stream Out Logs": Job.job_folders["stream_out"],
            "Stream Err Logs": Job.job_folders["stream_err"],
            "Rsync Logs": Job.job_folders["rsync"]
        }

        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

        SIGNALS.job_selected.connect(self.load_job)
    
    def load_job(self, job:Job):
        self.job = job
        self._fill_log_combo()
        self._fill_log_list()

    def _fill_log_combo(self):
        self.log_combo.clear()
        if self.job is None:
            return
        for log in self.log_dirs_dict.keys():
            self.log_combo.addItem(log)

    def _fill_log_list(self):
        self.log_list.clear()
        if self.job is None:
            return
        log_dir = self.log_dirs_dict[self.log_combo.currentText()]
        log_path = Path(self.job.get_folder()) / log_dir
        for file in log_path.glob("*.*"):
            self.log_list.addItem(file.name)

    def _create_widgets(self):
        self.log_combo = QComboBox()
        self.log_list = QListWidget()
        self.log_list.itemSelectionChanged.connect(self._log_file_selected)
        
    def _connect_widgets(self):
        self.log_combo.activated.connect(self._log_type_selected)

    def _create_layout(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.log_combo)
        vbox.addWidget(self.log_list, stretch=1)
        self.setLayout(vbox)

    def _log_type_selected(self, index):
        self._fill_log_list()
        # SIGNALS.log_type_selected.emit(renderer)

    def _log_file_selected(self):
        log_dir = self.log_dirs_dict[self.log_combo.currentText()]
        log_file = Path(self.job.get_folder()) / log_dir / self.log_list.currentItem().text()
        SIGNALS.log_file_selected.emit(log_file)


class LogDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

        SIGNALS.log_file_selected.connect(self._load_text)
        
    def _create_widgets(self):
        self.search_field = QLineEdit()
        self.text_field = QTextEdit()
    
    def _connect_widgets(self):
        self.search_field.textChanged.connect(self.do_find_highlight)

    def test(self, pattern):
        print(pattern)

    def _create_layout(self):
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Search: "))
        hbox.addWidget(self.search_field)
        vbox.addLayout(hbox)
        vbox.addWidget(self.text_field, stretch=1)
        self.setLayout(vbox)

    def _load_text(self, file:Path):
        log_text = ""
        if file.exists():
            log_text = file.read_text()

        self.text_field.setText(log_text)

    def do_find_highlight(self, pattern):
        cursor = self.text_field.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())
        cursor.clearSelection()

        if len(pattern) < 2:
            return
        
        # Setup the desired format for matches
        format = QTextCharFormat()
        format.setBackground(QBrush(QColor("red")))
        
        # Setup the regex engine
        re = QRegularExpression(pattern)
        i = re.globalMatch(self.text_field.toPlainText()) # QRegularExpressionMatchIterator

        # iterate through all the matches and highlight
        while i.hasNext():
            match = i.next() #QRegularExpressionMatch

            # Select the matched text and apply the desired format
            cursor.setPosition(match.capturedStart(), QTextCursor.MoveAnchor)
            cursor.setPosition(match.capturedEnd(), QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(format)

        self.text_field.setTextCursor(cursor)


class JobLogsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.job:Job = None
        
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

        SIGNALS.job_selected.connect(self.load_job)

    def load_job(self, job:Job):
        self.job = job
            
    def _create_widgets(self):
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setHandleWidth(15)
        self.splitter.setStretchFactor(3, 10)
        self.log_selection_widget = LogSelectionWidget()
        self.log_selection_widget.setMinimumWidth(180)
        self.log_display_widget = LogDisplayWidget()
    
    def _connect_widgets(self):
        pass

    def _create_layout(self):
        vbox = QVBoxLayout()
        #vbox.setContentsMargins(0,0,0,0)

        self.splitter.addWidget(self.log_selection_widget)
        self.splitter.addWidget(self.log_display_widget)

        vbox.addWidget(self.splitter, stretch=1)
        self.setLayout(vbox)

    def _save_clicked(self):
        self.job.write_job_files()
        self.job.create_rsync_push_file()
        self.job.set_ready_to_push(True)
        print("TODO: Check job settings, render config, scenes and linked files")