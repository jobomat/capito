import os
from pathlib import Path

from PySide2.QtWidgets import *
import pymel.core as pc

from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QHLine
import capito.maya.render.hlrs.utils as hlrsutils


class SceneStatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self._create_widgets()
        self._create_layout()
        self.update()

    def _create_widgets(self):
        self.startframe_label = QLabel()
        self.endframe_label = QLabel()
        self.rendercam_label = QLabel()

    def _create_layout(self):
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        hbox = QHBoxLayout()
        label = QLabel("Framerange:")
        label.setStyleSheet("font-weight: bold;")
        label.setMinimumWidth(80)
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
        label.setMinimumWidth(80)
        hbox.addWidget(label)
        hbox.addWidget(self.rendercam_label)
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
        self.dir_lineedit = QLineEdit()
        self.dir_lineedit.setEnabled(False)
        self.dir_lineedit.setText("")
        self.dir_lineedit.setPlaceholderText("Please select export folder")
        self.dir_lineedit.setStyleSheet("QLineEdit{color: grey;}")
        self.choose_folder_button = QPushButton("")
        icon = self.style().standardIcon(QStyle.SP_DirIcon)
        self.choose_folder_button.setIcon(icon)

        self.job_name_lineedit = QLineEdit()
        self.job_name_lineedit.setText(Path(pc.sceneName()).stem)

        self.renderlayer_widget = RenderLayerWidget()

        self.scene_status_widget = SceneStatusWidget()

        self.workspace_name_lineedit = QLineEdit()
        self.workspace_name_lineedit.setText("zmcjbomm_render")

        self.export_button = QPushButton("Export")
        self.export_button.setEnabled(False)
 
    def _connect_widgets(self):
        self.choose_folder_button.clicked.connect(self._set_job_folder)
        self.job_name_lineedit.textChanged.connect(self._check_job_dir)
        self.export_button.clicked.connect(self._export)

    def _create_layout(self):
        vbox = QVBoxLayout()

        dir_hbox = QHBoxLayout()
        label = QLabel("Export Folder:")
        label.setMinimumWidth(80)
        label.setStyleSheet("font-weight: bold;")
        dir_hbox.addWidget(label)
        dir_hbox.addWidget(self.dir_lineedit, stretch=1)
        dir_hbox.addWidget(self.choose_folder_button)
        vbox.addLayout(dir_hbox)

        jobname_hbox = QHBoxLayout()
        label = QLabel("Job Name:")
        label.setMinimumWidth(80)
        label.setStyleSheet("font-weight: bold;")
        jobname_hbox.addWidget(label)
        jobname_hbox.addWidget(self.job_name_lineedit, stretch=1)
        vbox.addLayout(jobname_hbox)

        vbox.addWidget(QHLine())
        vbox.addWidget(QLabel("Render Layers:"))
        vbox.addWidget(self.renderlayer_widget)

        vbox.addWidget(QHLine())
        vbox.addWidget(self.scene_status_widget)

        vbox.addWidget(self.workspace_name_lineedit) 
        vbox.addStretch()
        vbox.addWidget(self.export_button)
        #vbox.addWidget(QHLine())

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def _set_job_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Directory",
            str(pc.Workspace().path),
            QFileDialog.ShowDirsOnly
        )
        self.dir_lineedit.setText(folder)
        self._check_job_dir(False)

    def _check_job_dir(self, *arg):
        jobname = self.job_name_lineedit.text()
        folder = self.dir_lineedit.text()
        if not folder:
            self.statusBar().showMessage("Please specify an export folder.")
            return False
        if not jobname:
            self.statusBar().showMessage("Please specify a job name.")
            return False
        if (Path(folder) / jobname).exists():
            self.statusBar().showMessage("Subfolder with job name already exists.")
            return False
        self.statusBar().showMessage("Ready for export!")
        return True

    def _export(self):
        renderglobals = pc.PyNode("defaultRenderGlobals")
        startframe = int(renderglobals.startFrame.get())
        endframe = int(renderglobals.endFrame.get())
        folder = self.dir_lineedit.text()
        jobname = self.job_name_lineedit.text()
        renderlayers = self.renderlayer_widget.get_selected_renderlayers()
        workspace_name = self.workspace_name_lineedit.text()

        hlrsutils.create_shot_folders(folder, jobname)
        hlrsutils.export_ass_files(folder, jobname, startframe, endframe, renderlayers)
        hlrsutils.write_jobfiles(folder, jobname, workspace_name)

        resources = hlrsutils.collect_resources()
        hlrsutils.copy_resources(resources, Path(folder) / jobname / "resources")
        pathmap = hlrsutils.get_pathmap(resources)
        hlrsutils.write_pathmap(pathmap, Path(folder) / jobname)

    def closeEvent(self, event):
        for job in self.script_jobs:
            pc.scriptJob(kill=job)
    
        