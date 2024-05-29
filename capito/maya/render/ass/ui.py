import os
from pathlib import Path
from functools import partial
import tempfile

from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
import pymel.core as pc

from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QHLine
from capito.haleres.settings import Settings
from capito.haleres.job import Job
from capito.haleres.utils import is_valid_frame_list, create_frame_tuple_list, create_flat_frame_list
from capito.haleres.ui.job_list_widgets import ChooseJobWin
from capito.haleres.renderer import RendererProvider
from capito.maya.render.ass.tools import write_syncfile, parallel_ass_export


FIRST_COL_WIDTH = 120


class RenderCamWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self._create_widgets()
        self._create_layout()
        self.update()

    def _create_widgets(self):
        self.rendercam_label = QLabel() 

    def _create_layout(self):
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        hbox = QHBoxLayout()
        label = QLabel("Rendercam:")
        label.setStyleSheet("font-weight: bold;")
        label.setMinimumWidth(FIRST_COL_WIDTH)
        hbox.addWidget(label)
        hbox.addWidget(self.rendercam_label)
        hbox.addStretch()
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)

    def update(self):
        rendercams = [c for c in pc.ls(type='camera') if c.renderable.get()]
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
        vbox.setContentsMargins(0, 0, 0, 0)

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
class AssExporter(QMainWindow):
    def __init__(self, settings:Settings, host: str = None, parent=None):
        super().__init__(parent)
        self.host = host
        self.settings = settings
        self.update_status = True
        self.job:Job = None
        self.current_jobsize = 2
        self.current_walltime = 20

        self.renderer_provider = RendererProvider(settings)

        self.setWindowTitle(f"HLRS ASS Exporter")
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()
        self.statusBar().setStyleSheet("border-top: 1px solid grey")
        self.statusBar().showMessage("HLRS Job Exporter GUI...")
        self.setMinimumWidth(350)
        self.show()
        self.script_jobs = [
            pc.scriptJob(event=["idleVeryLow", self.update]),
            pc.scriptJob(event=["renderLayerChange", self.renderlayer_widget.update])
            #RenderSetupSelectionChanged
            #renderLayerChange
        ]

    def update(self):
        only_one_cam = self.rendercam_status_widget.update()
        checks_ok = self._perform_sanity_checks()
        if not only_one_cam:
            self.statusBar().showMessage("Please mark only one camera as renderable.")
        self.export_button.setEnabled(only_one_cam and checks_ok)    

    def _create_widgets(self):
        self.job_lineedit = QLineEdit()
        self.job_lineedit.setReadOnly(True)
        self.choose_job_button = QPushButton("")
        icon = self.style().standardIcon(QStyle.SP_FileDialogListView)
        self.choose_job_button.setIcon(icon)

        self.framelist_textedit = QLineEdit()
        renderglobals = pc.PyNode("defaultRenderGlobals")
        startframe = int(renderglobals.startFrame.get())
        endframe = int(renderglobals.endFrame.get())
        self.framelist_textedit.setText(f"{startframe}-{endframe}")
        self.framelist_textedit.setPlaceholderText("For Example: 12-34, 40-50")

        self.rendercam_status_widget = RenderCamWidget()
        
        self.renderlayer_widget = RenderLayerWidget()

        self.cache_dir_lineedit = QLineEdit()
        self.cache_dir_lineedit.setEnabled(False)
        self.cache_dir_lineedit.setText(tempfile.gettempdir())
        self.cache_dir_lineedit.setPlaceholderText("Caching dir not set")
        self.cache_dir_lineedit.setStyleSheet("QLineEdit{color: grey;}")
        self.choose_folder_button = QPushButton("")
        icon = self.style().standardIcon(QStyle.SP_DirIcon)
        self.choose_folder_button.setIcon(icon)

        self.parallel_export_checkbox = QCheckBox()

        self.renderer_combo = QComboBox()
        for renderer in [r for r in self.renderer_provider.renderers if r.startswith("Arnold")]:
            self.renderer_combo.addItem(renderer)

        self.hlrs_walltime_lineedit = QLineEdit()
        self.hlrs_walltime_lineedit.setText(str(self.current_walltime))

        self.hlrs_jobsize_lineedit = QLineEdit()
        self.hlrs_jobsize_lineedit.setText(str(self.current_jobsize))

        self.export_button = QPushButton("Export")
        self.export_button.setEnabled(False)
 
    def _connect_widgets(self):
        self.choose_job_button.clicked.connect(self._choose_job)
        self.choose_folder_button.clicked.connect(self._set_cache_folder)
        self.export_button.clicked.connect(self._export)
        self.hlrs_walltime_lineedit.textChanged.connect(self._validate_walltime)
        self.hlrs_walltime_lineedit.editingFinished.connect(self._approve_walltime)
        self.hlrs_jobsize_lineedit.textChanged.connect(self._validate_jobsize)
        self.hlrs_jobsize_lineedit.editingFinished.connect(self._approve_jobsize)

    def _create_layout(self):
        vbox = QVBoxLayout()

        job_hbox = QHBoxLayout()
        job_label = QLabel("Render Job:")
        job_label.setMinimumWidth(FIRST_COL_WIDTH)
        job_label.setStyleSheet("font-weight: bold;")
        job_hbox.addWidget(job_label)
        job_hbox.addWidget(self.job_lineedit)
        job_hbox.addWidget(self.choose_job_button)
        vbox.addLayout(job_hbox)

        cache_dir_hbox = QHBoxLayout()
        cache_dir_label = QLabel("Local Cache Dir:")
        cache_dir_label.setMinimumWidth(FIRST_COL_WIDTH)
        cache_dir_hbox.addWidget(cache_dir_label)
        cache_dir_hbox.addWidget(self.cache_dir_lineedit)
        cache_dir_hbox.addWidget(self.choose_folder_button)
        vbox.addLayout(cache_dir_hbox)
        
        parallel_export_hbox = QHBoxLayout()
        parallel_export_label = QLabel("Parallel Export:")
        parallel_export_label.setMinimumWidth(FIRST_COL_WIDTH)
        parallel_export_hbox.addWidget(parallel_export_label)
        parallel_export_hbox.addWidget(self.parallel_export_checkbox, stretch=1)
        vbox.addLayout(parallel_export_hbox)

        vbox.addWidget(QHLine())
        
        hbox = QHBoxLayout()
        label = QLabel("Framelist:")
        label.setStyleSheet("font-weight: bold;")
        label.setMinimumWidth(FIRST_COL_WIDTH)
        hbox.addWidget(label)
        hbox.addWidget(self.framelist_textedit, stretch=1)
        vbox.addLayout(hbox)

        vbox.addWidget(self.rendercam_status_widget)
        
        hbox = QHBoxLayout()
        rl_label = QLabel("Render Layers:")
        rl_label.setMinimumWidth(FIRST_COL_WIDTH)
        rl_label.setStyleSheet("font-weight: bold;")
        hbox.addWidget(rl_label)
        hbox.addWidget(self.renderlayer_widget, stretch=1)
        vbox.addLayout(hbox)

        vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        label = QLabel("Renderer")
        label.setMinimumWidth(FIRST_COL_WIDTH)
        label.setStyleSheet("font-weight: bold;")
        hbox.addWidget(label)
        hbox.addWidget(self.renderer_combo, stretch=1)
        vbox.addLayout(hbox)
        
        hbox = QHBoxLayout()
        label = QLabel("HLRS Walltime (min)")
        label.setMinimumWidth(FIRST_COL_WIDTH)
        label.setStyleSheet("font-weight: bold;")
        hbox.addWidget(label)
        hbox.addWidget(self.hlrs_walltime_lineedit)
        vbox.addLayout(hbox)

        hbox = QHBoxLayout()
        label = QLabel("HLRS Frames per Node")
        label.setMinimumWidth(FIRST_COL_WIDTH)
        label.setStyleSheet("font-weight: bold;")
        hbox.addWidget(label)
        hbox.addWidget(self.hlrs_jobsize_lineedit)
        vbox.addLayout(hbox)
 
        vbox.addStretch()
        vbox.addWidget(QHLine())
        vbox.addWidget(QLabel("Before clicking export, make sure to check your render settings\n(Samples etc.) and save the scene!"))
        vbox.addWidget(self.export_button)
        #vbox.addWidget(QHLine())

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def _validate_walltime(self, value):
        mini = 1
        maxi = 90
        if not value:
            return
        try:
            self.current_walltime = int(value)
        except:
            pass
        self.hlrs_walltime_lineedit.setText(
            str(min(maxi, max(int(self.current_walltime), mini)))
        )

    def _approve_walltime(self):
        self.hlrs_walltime_lineedit.setText(str(self.current_walltime))
    
    def _validate_jobsize(self, value):
        mini = 1
        maxi = 25
    
        if not value:
            return
        try:
            self.current_jobsize = int(value)
        except:
            pass
        self.hlrs_jobsize_lineedit.setText(
            str(min(maxi, max(int(self.current_jobsize), mini)))
        )
    
    def _approve_jobsize(self):
        self.hlrs_jobsize_lineedit.setText(str(self.current_jobsize))

    def _choose_job(self):
        share = "cg1"
        ChooseJobWin(self.settings, self._set_job, share)
    
    def _set_job(self, job):
        self.job = job
        self.job_lineedit.setText(job.name)
    
    def _set_cache_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Caching Directory",
            str(pc.Workspace().path),
            QFileDialog.ShowDirsOnly
        )
        self.cache_dir_lineedit.setText(folder)

    def _perform_sanity_checks(self, *arg):
        if self.job is None:
            self.statusBar().showMessage("Please select or create a render job.")
            return False
        framelist = self.framelist_textedit.text().strip()
        if not framelist:
            self.statusBar().showMessage("Please specify a valid frame list.")
            return False
        if not is_valid_frame_list(framelist):
            self.statusBar().showMessage("Provided frame list is not valid.")
            return False
        if not self.renderlayer_widget.get_selected_renderlayers():
            self.statusBar().showMessage("Please select at least one render layer.")
            return False
        if self.update_status:
            self.statusBar().showMessage("Ready for export!")
        return True

    def _export(self):
        cache_dir = self.cache_dir_lineedit.text()
        renderlayers = self.renderlayer_widget.get_selected_renderlayers()
        
        self.job.framelist = self.framelist_textedit.text()
        # WONKY: if project is not on the same share as the seleced job strange things happen
        write_syncfile(self.job)
        self.job.create_rsync_push_file()
        print("Created rsync push file.")
        self.job.jobsize = int(self.hlrs_jobsize_lineedit.text())
        self.job.walltime_minutes = int(self.hlrs_walltime_lineedit.text())
        self.job.renderer = self.renderer_provider.renderers[self.renderer_combo.currentText()]
        self.job.save_job_settings()
        self.job.save_renderer_config()
        print("Saved renderer config file.")
        self.job.write_pathmap_json()
        print("Created pathmap.json.")
        if self.parallel_export_checkbox.isChecked():
            self.statusBar().showMessage("Subprocess export... See Script Editor.")
            parallel_ass_export(pc.sceneName(), self.job, renderlayers, cache_dir)
            return
        self._single_core_export(renderlayers, cache_dir)

    def _single_core_export(self, renderlayers, cache_dir):
        self.update_status = False
        flat_frame_list = create_flat_frame_list(self.framelist_textedit.text())
        num_layers = len(renderlayers)
        for i, rl in enumerate(renderlayers, start=1):
            rl.setCurrent()
            self.statusBar().showMessage(f"Export Layer {i} of {num_layers} ({rl.name()})")
            print(f"Export Layer {i} of {num_layers} ({rl.name()})")
            print(f"Ass files will be written to: {self.job.get_folder('scenes')}")
            pc.other.arnoldExportAss(
                f=f"{self.job.get_folder('scenes')}/{self.job.name}_<RenderLayer>.ass",
                startFrame=flat_frame_list[0], endFrame=flat_frame_list[-1],
                preserveReferences=True
            )
        self.job.write_job_files()
        self.job.set_ready_to_push(True)
        self.statusBar().showMessage("Export completed!")

    def closeEvent(self, event):
        for job in self.script_jobs:
            pc.scriptJob(kill=job)
    
        