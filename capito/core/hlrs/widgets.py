from functools import partial
from pathlib import Path
from time import sleep

from PySide2.QtCore import QObject, Signal
from PySide2.QtGui import QIntValidator, Qt   # pylint:disable=wrong-import-order
from PySide2.QtWidgets import *

from capito.core.ui.widgets import QHLine
import capito.core.hlrs.bridge as bridge


def message(message:str):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(message)
        msgBox.setWindowTitle("Info")
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec()


class ShareWidget(QWidget):
    shareChanged = Signal(str)

    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout()
        hbox.setMargin(0)
        self.buttons = {
            share: {"button": QPushButton(share), "letter": letter}
            for share, letter in bridge.DRIVE_MAP.items()
        }
        hbox.addWidget(QLabel("Share: "))
        for share, data in self.buttons.items():
            hbox.addWidget(data["button"])
            data["button"].clicked.connect(partial(self.change_share, share))
        hbox.addStretch()
        self.setLayout(hbox)
    
    def change_share(self, share:str):
        for s, data in self.buttons.items():
            data["button"].setStyleSheet(
                f"background-color: {'#666' if s == share else '#333'};"
            )
        self.shareChanged.emit(self.buttons[share]["letter"])


class JobListWidget(QWidget):
    jobCreated = Signal()
    jobSelected = Signal(str)

    def __init__(self):
        super().__init__()
        self.hlrs_folder: Path = None
        vbox = QVBoxLayout()
        vbox.setMargin(0)

        self.joblist = QListWidget()
        self.joblist.itemClicked.connect(self.job_selected)
        vbox.addWidget(QLabel("Joblist"))
        vbox.addWidget(self.joblist, stretch=1)

        hbox = QHBoxLayout()
        add_job_btn = QPushButton("New Job")
        add_job_btn.clicked.connect(self.add_job)
        hbox.addWidget(add_job_btn)
        hbox.addStretch()

        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def job_selected(self, job:QListWidgetItem):
        self.jobSelected.emit(job.text())

    def list_hlrs_jobdir(self, share:str):
        self.hlrs_folder = Path(share) / "hlrs"
        foldernames = [f for f in self.hlrs_folder.iterdir() if f.is_dir()]
        self.joblist.clear()
        for f in foldernames:
            self.joblist.addItem(str(f.name))

    def add_job(self):
        if not self.hlrs_folder:
            message("Please select a share first.")
            return
        text, ok = QInputDialog().getText(
            self, "Add new Job",
            "Job name:", QLineEdit.Normal
        )
        if ok:
            text = text.strip()
            if not text:
                message(f"Please specify a job name.\n Job creation aborted.")
                return
            existing_names = [f.name for f in self.hlrs_folder.iterdir() if f.is_dir()]
            if text in existing_names:
                message(f"Job name '{text}' already exists.\n Job creation aborted.")
                return
            new_dir = self.hlrs_folder / text
            new_dir.mkdir()
            (new_dir / "jobs").mkdir()
            (new_dir / "scenes").mkdir()
            (new_dir / "output").mkdir()
            self.jobCreated.emit()
    
    


class FileTransferWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.filelist = []
        self.current_share = ""
        self.current_job = ""
        # self.init_filelist()
        vbox = QVBoxLayout()
        vbox.setMargin(0)

        vbox.addWidget(QLabel("Linked Files to transfer (textures, alembics, linked ass...)"))
        self.filelist_widget = QListWidget()
        self.filelist_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        vbox.addWidget(self.filelist_widget, stretch=1)

        hbox = QHBoxLayout()
        add_file_btn = QPushButton("Add File(s)")
        add_file_btn.clicked.connect(self.add_files)
        hbox.addWidget(add_file_btn)
        remove_file_btn = QPushButton("Remove selected")
        remove_file_btn.clicked.connect(self.remove_selected_files)
        hbox.addWidget(remove_file_btn)
        hbox.addStretch()

        vbox.addLayout(hbox)
        self.setLayout(vbox)
    
    def add_files(self):
        """add files to filelist.txt"""
        files = QFileDialog.getOpenFileNames(
            self,
            "Select one or more files to add",
            self.current_share
        )
        if files:
            self.filelist.extend(files[0])
            self.filelist = list(set(self.filelist))
            self.write_filelist()
        self.rebuild_filelist_widget()

    def iter_file_items(self):
        for i in range(self.filelist_widget.count()):
            yield self.filelist_widget.item(i)

    def remove_selected_files(self):
        """remove from filelist.txt. (No deletition of files taking place)"""
        selected_items = self.filelist_widget.selectedItems()
        for item in selected_items:
            self.filelist_widget.takeItem(self.filelist_widget.row(item))
        self.filelist = [item.text() for item in self.iter_file_items()]
        self.write_filelist()

    def write_filelist(self):
        """write filelist.txt residing in a job-folder."""
        (Path(self.current_share) / "hlrs" / self.current_job / "filelist.txt").write_text(
            "\n".join(self.filelist), encoding="UTF-8"
        )

    def read_filelist(self):
        """read filelist.txt residing in a job-folder."""
        self.filelist = []
        fl = Path(self.current_share) / "hlrs" / self.current_job / "filelist.txt"
        if not fl.exists():
            return
        self.filelist = fl.read_text(encoding="UTF-8").split("\n")

    def set_current_share(self, share:str):
        self.current_share = share
        self.filelist_widget.clear()

    def set_current_job(self, job:str):
        self.current_job = job
        
    def rebuild_filelist_widget(self):
        self.filelist_widget.clear()
        self.filelist_widget.addItems(self.filelist)


class RendererWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        hbox = QHBoxLayout()
        hbox.setMargin(0)

        self.renderer_combo = QComboBox()
        self.renderer_combo.addItems(parent.hlrs_vars["renderers"])
        hbox.addWidget(self.renderer_combo)

        hbox.addStretch()

        self.startframe_label = QLabel("Start frame:")
        hbox.addWidget(self.startframe_label)
        self.startframe_input = QLineEdit()
        self.startframe_input.setValidator(QIntValidator())
        self.startframe_input.setMaximumWidth(80)
        self.startframe_input.setText("1")
        hbox.addWidget(self.startframe_input)

        self.endframe_label = QLabel("End frame:")
        hbox.addWidget(self.endframe_label)
        self.endframe_input = QLineEdit()
        self.endframe_input.setMaximumWidth(80)
        self.endframe_input.setValidator(QIntValidator())
        self.endframe_input.setText("100")
        hbox.addWidget(self.endframe_input)

        self.jobsize_label = QLabel("Frames per node:")
        hbox.addWidget(self.jobsize_label)
        self.jobsize_input = QLineEdit()
        self.jobsize_input.setValidator(QIntValidator(1,9))
        self.jobsize_input.setText("2")
        self.jobsize_input.setMaxLength(1)
        self.jobsize_input.setMaximumWidth(30)
        hbox.addWidget(self.jobsize_input)

        self.setLayout(hbox)


class MainWidget(QWidget):
    """QWidget containing HLRS Widgets and Layouts."""
    def __init__(self, parent):
        super().__init__()
        self.bridge = bridge.Bridge()
        self.hlrs_vars = self.bridge.get_base_infos()

        vbox = QVBoxLayout()
        vbox.setMargin(0)

        share_widget = ShareWidget()
        vbox.addWidget(share_widget)

        vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        
        share_widget.shareChanged.connect(self.on_share_change)
        self.joblist_widget = JobListWidget()
        self.joblist_widget.setMaximumWidth(150)
        self.joblist_widget.jobCreated.connect(self.on_share_change)
        self.joblist_widget.jobSelected.connect(self.on_job_selected)

        hbox.addWidget(self.joblist_widget)

        self.file_transfer_widget = FileTransferWidget()
        hbox.addWidget(self.file_transfer_widget, stretch=1)

        vbox.addLayout(hbox)

        vbox.addWidget(QHLine())

        self.renderer_widget = RendererWidget(self)
        vbox.addWidget(self.renderer_widget)

        vbox.addWidget(QHLine())
        
        action_button_hbox = QHBoxLayout()
        self.status_label = QLabel("To start please select a share.")
        action_button_hbox.addWidget(self.status_label)
        action_button_hbox.addStretch()
        
        file_creation_btn = QPushButton("Create Files")
        file_creation_btn.clicked.connect(self.create_files)
        
        action_button_hbox.addWidget(file_creation_btn)
        
        transfer_btn = QPushButton("Transfer Files")
        transfer_btn.clicked.connect(self.push_transfer_files)
        
        action_button_hbox.addWidget(transfer_btn)
        vbox.addLayout(action_button_hbox)

        self.setLayout(vbox)

    def on_share_change(self, share:str=None):
        """User clicked on one of the share buttons."""
        if share is not None:
            self.current_hlrs_folder = share
        self.joblist_widget.list_hlrs_jobdir(self.current_hlrs_folder)
        self.file_transfer_widget.set_current_share(self.current_hlrs_folder)
        self.status_label.setText("Select or create a job.")

    def on_job_selected(self, job: str):
        """User selected a job from joblist."""
        self.file_transfer_widget.set_current_job(job)
        self.file_transfer_widget.read_filelist()
        self.file_transfer_widget.rebuild_filelist_widget()

    def push_transfer_files(self):
        rsync_file = self.get_rsync_file()
        sync_file = str(rsync_file).replace(
            self.current_hlrs_folder,
            f"{bridge.MOUNT_MAP[self.current_hlrs_folder]}/"
        ).replace("\\", "/")

        self.status_label.setText("Transfer in Progress...")
        self.status_label.repaint()
        result = self.bridge.push_files(sync_file)
        self.status_label.setText("Transfer finished")

    def create_files(self):
        linkfiles = self.file_transfer_widget.filelist
        jobdir = str(
            Path(self.current_hlrs_folder) / "hlrs" / self.file_transfer_widget.current_job
        ).replace(":",":\\")
        linkfiles.append(jobdir)
        
        rsync_list = bridge.create_rsync_list(linkfiles)

        rsync_file = self.get_rsync_file()
        rsync_file.write_text("\n".join(rsync_list), encoding="UTF-8")

        bridge.create_job_files(
            self.hlrs_vars["ws_name"],
            self.current_hlrs_folder,
            self.renderer_widget.renderer_combo.currentText(),
            self.file_transfer_widget.current_job,
            int(self.renderer_widget.startframe_input.text()),
            int(self.renderer_widget.endframe_input.text()),
            int(self.renderer_widget.jobsize_input.text())
        )
        

    def get_rsync_file(self):
        return (
            Path(self.current_hlrs_folder) / 
            "hlrs" /
            self.file_transfer_widget.current_job /
            "rsync_list.txt"
        )