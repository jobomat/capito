from typing import Any

from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

import pymel.core as pc

from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import IterableListWidget
from capito.core.ui.widgets import QHLine


class DriverListWidget(QWidget):
    driver_selected = Signal(pc.nodetypes.AiAOVDriver)

    def __init__(self):
        super().__init__()
        self.setMaximumHeight(60)
        self.add_button = QPushButton("Add Driver")
        self.driver_list_widget = IterableListWidget()
        self.driver_list_widget.itemClicked.connect(self._driver_selected)
        
        vbox = QVBoxLayout()
        
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(self.driver_list_widget)
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.add_button)
        self.setLayout(vbox)

        self.update()

    def update(self):
        self.driver_list_widget.clear()
        exr_drivers = [
            d for d in pc.ls(type="aiAOVDriver")
            if d.aiTranslator.get() == "exr"
        ]
        for driver in exr_drivers:
            self.add_driver_to_list(driver)

    def add_driver_to_list(self, driver):
        item = QListWidgetItem()
        item.driver = driver
        self.set_list_name(item)
        # item.setCheckState(Qt.Unchecked)
        self.driver_list_widget.addItem(item)

    def set_list_name(self, item:QListWidgetItem):
        driver = item.driver
        node_name = driver.name()
        prefix = driver.prefix.get()
        name_info = "default"
        if node_name != "defaultArnoldDriver":
            if prefix:
                name_info = prefix
            else: 
                name_info = f"driver_{len(pc.ls(type='aiAOVDriver')) - 2}"
                driver.prefix.set(name_info)
        item.setText(f"{node_name} ({name_info})")
    
    def _driver_selected(self):
        driver = self.driver_list_widget.selectedItems()[0].driver
        self.driver_selected.emit(driver)


class DriverSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.compression_names = [
            "none", "rle", "zips", "zip", "piz", "pxr24", "b44", "b44a", "dwaa", "dwab"
        ]
        self.current_driver = None
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.prefix_lineedit = QLineEdit("")
        self.compression_combobox = QComboBox()
        for c in self.compression_names:
            self.compression_combobox.addItem(c)
        self.merge_aovs_checkbox = QCheckBox()
        self.half_precision_checkbox = QCheckBox()

    def _connect_widgets(self):
        self.prefix_lineedit.textChanged.connect(self.update_driver_prefix)
        self.compression_combobox.currentTextChanged.connect(self.update_driver_compression)
        self.merge_aovs_checkbox.stateChanged.connect(self.update_driver_merge)
        self.half_precision_checkbox.stateChanged.connect(self.update_driver_precision)

    def update_driver_prefix(self, text):
        if not self.current_driver:
            return
        self.current_driver.prefix.set(text)

    def update_driver_compression(self, text):
        if not self.current_driver:
            return
        self.current_driver.exrCompression.set(self.compression_names.index(text))

    def update_driver_merge(self, state):
        if not self.current_driver:
            return
        self.current_driver.mergeAOVs.set(bool(state))

    def update_driver_precision(self, state):
        if not self.current_driver:
            return
        self.current_driver.halfPrecision.set(bool(state))

    def _create_layout(self):
        grid = QGridLayout()
        grid.setContentsMargins(0,0,0,0)
        widgets = [
            [QLabel("Name"), self.prefix_lineedit],
            [QLabel("Compression"), self.compression_combobox],
            [QLabel("Merge AOVs"), self.merge_aovs_checkbox],
            [QLabel("Half Precision"), self.half_precision_checkbox]
        ]
        for row, widget_list in enumerate(widgets, start=1):
            for col, widget in enumerate(widget_list, start=1):
                grid.addWidget(widget, row, col)

        self.setLayout(grid)

    def update(self, driver:pc.nodetypes.AiAOVDriver):
        self.current_driver = driver
        self.prefix_lineedit.setText(driver.prefix.get())
        self.prefix_lineedit.setEnabled(driver.name() != "defaultArnoldDriver")
        self.compression_combobox.setCurrentIndex(driver.exrCompression.get())
        self.merge_aovs_checkbox.setChecked(driver.mergeAOVs.get())
        self.half_precision_checkbox.setChecked(driver.halfPrecision.get())


class AOVListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.aov_list_widget = IterableListWidget()
        self.aov_list_widget.setSpacing(3)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(self.aov_list_widget)

        self.setLayout(vbox)

    def update(self, driver):
        self.aov_list_widget.clear()
        for aov in pc.ls(type="aiAOV"):
            item = QListWidgetItem(aov.attr("name").get())
            item.aov = aov
            item.driver = None
            item.setCheckState(Qt.Unchecked)
            if driver in item.aov.listConnections():
                item.setCheckState(Qt.Checked)
                item.driver = driver
            self.aov_list_widget.addItem(item)        


@bind_to_host
class OutputDriverManager(QMainWindow):
    def __init__(self, host, parent):
        super().__init__(parent)
        self.setWindowTitle("Screw the Driver")
        self._create_widgets()
        self._connect_widgets()
        self._create_layouts()
        
        
    def _create_widgets(self):
        self.driver_list_widget = DriverListWidget()
        self.driver_settings_widget = DriverSettingsWidget()
        self.aov_list_widget = AOVListWidget()
        
    def _connect_widgets(self):
        self.driver_list_widget.driver_selected.connect(self.driver_settings_widget.update)
        self.driver_list_widget.driver_selected.connect(self.aov_list_widget.update)
        
    def _create_layouts(self):
        vbox = QVBoxLayout()
        
        label = QLabel("Drivers (EXR only)")
        label.setStyleSheet("QLabel {font-weight: bold;}")
        vbox.addWidget(label)
        vbox.addWidget(self.driver_list_widget)
        vbox.addWidget(QHLine())
        label = QLabel("Driver Settings")
        label.setStyleSheet("QLabel {font-weight: bold;}")
        vbox.addWidget(label)
        vbox.addWidget(self.driver_settings_widget)
        vbox.addWidget(QHLine())
        label = QLabel("AOVs for Driver")
        label.setStyleSheet("QLabel {font-weight: bold;}")
        vbox.addWidget(label)
        vbox.addWidget(self.aov_list_widget)
            
        cw = QWidget()
        cw.setLayout(vbox)
        self.setCentralWidget(cw)


OutputDriverManager()