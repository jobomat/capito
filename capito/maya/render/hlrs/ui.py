import os
from pathlib import Path

from PySide2.QtWidgets import *
import pymel.core as pc

from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QHLine
from capito.core.hlrs.utils import create_job_folders
from capito.maya.render.hlrs.tools import write_syncfile, parallel_ass_export


FIRST_COL_WIDTH = 100


class SceneStatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.hlrs_folder = Path(pc.sceneName()[:3]) / "hlrs"
        self.setContentsMargins(0, 0, 0, 0)
        self._create_widgets()
        self._create_layout()
        self.update()

    def _create_widgets(self):
        self.startframe_label = QLabel()
        self.endframe_label = QLabel()
        self.rendercam_label = QLabel() 
        self.hlrs_folder_label = QLabel(str(self.hlrs_folder))

    def _create_layout(self):
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        hbox = QHBoxLayout()
        label = QLabel("Framerange:")
        label.setStyleSheet("font-weight: bold;")
        label.setMinimumWidth(FIRST_COL_WIDTH)
        hbox.addWidget(label)
        hbox.addWidget(self.startframe_label)
        label = QLabel(" - ")
        hbox.addWidget(label)
        hbox.addWidget(self.endframe_label)
        hbox.addStretch()
        vbox.addLayout(hbox)

        hbox = QHBoxLayout()
        label = QLabel("Rendercam:")
        label.setStyleSheet("font-weight: bold;")
        label.setMinimumWidth(FIRST_COL_WIDTH)
        hbox.addWidget(label)
        hbox.addWidget(self.rendercam_label)
        hbox.addStretch()
        vbox.addLayout(hbox)
        
        hbox = QHBoxLayout()
        label = QLabel("HLRS Folder:")
        label.setStyleSheet("font-weight: bold;")
        label.setMinimumWidth(FIRST_COL_WIDTH)
        hbox.addWidget(label)
        hbox.addWidget(self.hlrs_folder_label)
        hbox.addStretch()
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)

    def update(self):
        renderglobals = pc.PyNode("defaultRenderGlobals")
        startframe = int(renderglobals.startFrame.get())
        endframe = int(renderglobals.endFrame.get())
        rendercams = [c for c in pc.ls(type='camera') if c.renderable.get()]
        self.startframe_label.setText(f"{startframe:04d}")
        self.endframe_label.setText(f"{endframe:04d}")
        rendercam_label = ""
        status = False
        if len(rendercams) > 1:
            rendercam_label = "More than one render Cam!"
            self.rendercam_label.setStyleSheet("color: red")
        elif not rendercams:
            rendercam_label = "No render Cam!"
            self.rendercam_label.setStyleSheet("color: red")
        else:
            rendercam_label = f"{rendercams[0]}"
            self.rendercam_label.setStyleSheet("color: rgb(187,187,187);")
            status = True
        self.rendercam_label.setText(rendercam_label)
        
        return status


class RenderLayerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self._create_widgets()
        self._create_layout()
        self.update()

    def _create_widgets(self):
        pass

    def _create_layout(self):
        vbox = QVBoxLayout()

        self.layer_vbox = QVBoxLayout()
        self.layer_vbox.addWidget(QLabel("TEST"))
        vbox.addLayout(self.layer_vbox)

        self.setLayout(vbox)

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update(self):
        self.renderlayers = [rl for rl in pc.ls(type='renderLayer')]
        self._clear_layout(self.layer_vbox)
        for rl in self.renderlayers:
            name = rl.name()
            name = "masterLayer" if name == "defaultRenderLayer" else name[3:]
            cb = QCheckBox(name)
            cb.rl = rl
            self.layer_vbox.addWidget(cb)

    def _get_checkboxes(self):
        return (self.layer_vbox.itemAt(i).widget() for i in range(self.layer_vbox.count()))

    def get_selected_renderlayers(self):
        return [cb.rl for cb in self._get_checkboxes() if cb.isChecked()]




@bind_to_host
class HlrsExporter(QMainWindow):
    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.host = host
        self.setWindowTitle(f"HLRS Exporter")
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()
        self.statusBar().setStyleSheet("border-top: 1px solid grey")
        self.statusBar().showMessage("HLRS Exporter GUI...")
        self.setMinimumWidth(300)
        self.show()
        self.script_jobs = [
            pc.scriptJob(event=["idleVeryLow", self.update]),
            pc.scriptJob(event=["renderLayerChange", self.renderlayer_widget.update])
            #RenderSetupSelectionChanged
            #renderLayerChange
        ]

    def update(self):
        only_one_cam = self.scene_status_widget.update()
        jobdir_ok = self._check_job_dir()
        if not only_one_cam:
            self.statusBar().showMessage("Please mark only one camera as renderable.")
        self.export_button.setEnabled(only_one_cam and jobdir_ok)
        

    def _create_widgets(self):
        self.job_name_lineedit = QLineEdit()
        self.job_name_lineedit.setText(Path(pc.sceneName()).stem)

        self.renderlayer_widget = RenderLayerWidget()

        self.scene_status_widget = SceneStatusWidget()

        self.cache_dir_lineedit = QLineEdit()
        self.cache_dir_lineedit.setEnabled(False)
        self.cache_dir_lineedit.setText("")
        self.cache_dir_lineedit.setPlaceholderText("Caching dir not set")
        self.cache_dir_lineedit.setStyleSheet("QLineEdit{color: grey;}")
        self.choose_folder_button = QPushButton("")
        icon = self.style().standardIcon(QStyle.SP_DirIcon)
        self.choose_folder_button.setIcon(icon)


        self.export_button = QPushButton("Export")
        self.export_button.setEnabled(False)
 
    def _connect_widgets(self):
        self.choose_folder_button.clicked.connect(self._set_cache_folder)
        self.job_name_lineedit.textChanged.connect(self._check_job_dir)
        self.export_button.clicked.connect(self._export)

    def _create_layout(self):
        vbox = QVBoxLayout()

        jobname_hbox = QHBoxLayout()
        label = QLabel("Job Name:")
        label.setMinimumWidth(FIRST_COL_WIDTH)
        label.setStyleSheet("font-weight: bold;")
        jobname_hbox.addWidget(label)
        jobname_hbox.addWidget(self.job_name_lineedit, stretch=1)
        vbox.addLayout(jobname_hbox)

        vbox.addWidget(QHLine())
        vbox.addWidget(QLabel("Render Layers:"))
        vbox.addWidget(self.renderlayer_widget)

        vbox.addWidget(QHLine())
        vbox.addWidget(self.scene_status_widget)
        vbox.addWidget(QHLine())
        cache_dir_hbox = QHBoxLayout()
        cache_dir_label = QLabel("Local Cache Dir:")
        cache_dir_label.setMinimumWidth(FIRST_COL_WIDTH)
        cache_dir_hbox.addWidget(cache_dir_label)
        cache_dir_hbox.addWidget(self.cache_dir_lineedit)
        cache_dir_hbox.addWidget(self.choose_folder_button)
        vbox.addLayout(cache_dir_hbox)
        vbox.addWidget(QHLine())
 
        vbox.addStretch()
        vbox.addWidget(self.export_button)
        #vbox.addWidget(QHLine())

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)
    
    def _set_cache_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Caching Directory",
            str(pc.Workspace().path),
            QFileDialog.ShowDirsOnly
        )
        self.cache_dir_lineedit.setText(folder)

    def _check_job_dir(self, *arg):
        jobname = self.job_name_lineedit.text()
        if not jobname:
            self.statusBar().showMessage("Please specify a job name.")
            return False
        if (self.scene_status_widget.hlrs_folder / jobname).exists():
            self.statusBar().showMessage("Subfolder with job name already exists.")
            return False
        if not self.renderlayer_widget.get_selected_renderlayers():
            self.statusBar().showMessage("Please select at least one render layer.")
            return False
        self.statusBar().showMessage("Ready for export!")
        return True

    def _export(self):
        renderglobals = pc.PyNode("defaultRenderGlobals")
        startframe = int(renderglobals.startFrame.get())
        endframe = int(renderglobals.endFrame.get())
        jobname = self.job_name_lineedit.text()
        folder = self.scene_status_widget.hlrs_folder / jobname
        renderlayers = self.renderlayer_widget.get_selected_renderlayers()
        cache_dir = self.cache_dir_lineedit.text()

        export_file = str(folder / "scenes" / jobname)
        if cache_dir:
            export_file = str(Path(cache_dir) / jobname / "scenes" / jobname)

        create_job_folders(folder)
        write_syncfile(folder)
        parallel_ass_export(export_file, startframe, endframe, renderlayers)

    def closeEvent(self, event):
        for job in self.script_jobs:
            pc.scriptJob(kill=job)
    
        