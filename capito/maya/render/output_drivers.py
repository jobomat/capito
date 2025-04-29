from typing import TypeAlias

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

import pymel.core as pc
from pymel.core.general import MayaNodeError

from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import IterableListWidget
from capito.core.ui.widgets import QHLine


DEFAULT_RENDER_GLOBALS = None

AiAOVDriver: TypeAlias  = pc.nodetypes.AiAOVDriver

def list_drivers(output_format:str="exr") -> list:
    return [
        d for d in pc.ls(type="aiAOVDriver")
        if d.aiTranslator.get() == output_format
    ]


def get_short_driver_name(driver:AiAOVDriver) -> str:
    name = driver.prefix.get().split(">")[-1]
    return name.lstrip("_")


def get_full_driver_name(short_name:str) -> str:
    prefix = DEFAULT_RENDER_GLOBALS.imageFilePrefix.get()
    if prefix is None:
        return short_name
    return f"{prefix}_{short_name}"


def get_free_driver_index(aov):
    for i in range(aov.attr("outputs").numElements()):
        if not aov.attr(f"outputs[{i}].driver").listConnections():
            return i
    return aov.attr("outputs").numElements()


def get_aov_attr_for_driver(aov, driver):
    for i in range(aov.attr("outputs").numElements()):
        if driver in aov.attr(f"outputs[{i}].driver").listConnections():
            return aov.attr(f"outputs[{i}].driver")


class DriverListWidget(QWidget):
    driver_selected = Signal(QListWidgetItem)

    def __init__(self):
        super().__init__()
        self.dad = pc.PyNode("defaultArnoldDriver")
        self.setMaximumHeight(100)
        self.add_button = QPushButton("Add Driver")
        self.add_button.clicked.connect(self.add_driver)
        self.remove_button = QPushButton("Delete Selected Driver")
        self.remove_button.clicked.connect(self.remove_driver)
        self.driver_list_widget = IterableListWidget()
        self.driver_list_widget.itemClicked.connect(self._driver_selected)
        self.driver_list_widget.itemDoubleClicked.connect(self._select_driver_node)
                
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        
        vbox.addWidget(self.driver_list_widget)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,1,0,3)
        hbox.addWidget(self.add_button)
        hbox.addWidget(self.remove_button)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.update()

    def update(self, select=None):
        self.driver_list_widget.clear()
        for driver in list_drivers():
            self.add_driver_to_list(driver, driver == select)

    def add_driver_to_list(self, driver, select=False):
        item = QListWidgetItem()
        item.driver = driver
        self.set_list_name(item)
        self.driver_list_widget.addItem(item)
        if select:
            item.setSelected(True)
            self.driver_selected.emit(item)

    def set_list_name(self, item:QListWidgetItem):
        driver = item.driver
        node_name = driver.name()
        prefix = get_short_driver_name(driver)
        name_info = "default"
        if node_name != "defaultArnoldDriver":
            if prefix:
                name_info = prefix
            else: 
                name_info = f"driver{len(pc.ls(type='aiAOVDriver')) - 2}"
                driver.prefix.set(name_info)
        item.setText(f"{node_name} ({name_info})")

    def add_driver(self):
        driver = pc.createNode("aiAOVDriver")
        driver.exrCompression.set(self.dad.exrCompression.get())
        driver.mergeAOVs.set(self.dad.mergeAOVs.get())
        driver.halfPrecision.set(self.dad.halfPrecision.get())
        self.update(select=driver)

    def remove_driver(self):
        driver = self.driver_list_widget.selectedItems()[0].driver
        if driver.name() == "defaultArnoldDriver":
            pc.warning("Cannot delete the default Arnold driver.")
            return
        pc.delete(driver)
        self.update()
    
    def _driver_selected(self):
        item = self.driver_list_widget.selectedItems()[0]
        self.driver_selected.emit(item)

    def _select_driver_node(self):
        driver = self.driver_list_widget.selectedItems()[0].driver
        if driver:
            pc.select(driver, r=True)


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
        self.prefix_lineedit.setPlaceholderText("Please specify a name (except on default driver).")
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
        node_name = self.current_driver.name()
        if not self.current_driver or node_name == "defaultArnoldDriver":
            return
        self.current_driver.prefix.set(get_full_driver_name(text))
        self.current_item.setText(f"{node_name} ({text})")

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

    def update(self, item:QListWidgetItem):
        driver:AiAOVDriver = item.driver
        self.current_item = item
        self.current_driver = driver
        self.prefix_lineedit.setText(get_short_driver_name(driver))
        self.prefix_lineedit.setEnabled(driver.name() != "defaultArnoldDriver")
        self.compression_combobox.setCurrentIndex(driver.exrCompression.get())
        self.merge_aovs_checkbox.setChecked(driver.mergeAOVs.get())
        self.half_precision_checkbox.setChecked(driver.halfPrecision.get())


class AOVListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.aov_list_widget = IterableListWidget()
        self.aov_list_widget.setStyleSheet( "QListWidget::item { border-bottom: 1px solid #999999; padding-top: 2px; padding-bottom: 2px;}" )
        self.aov_list_widget.itemChanged.connect(self.edit_aov)
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(self.aov_list_widget)

        self.setLayout(vbox)

    def update(self, item:QListWidgetItem):
        driver:AiAOVDriver = item.driver
        self.aov_list_widget.clear()
        for aov in pc.ls(type="aiAOV"):
            item = QListWidgetItem(aov.attr("name").get())
            item.aov = aov
            item.driver = driver
            item.setCheckState(Qt.Unchecked)
            if driver in item.aov.listConnections():
                item.setCheckState(Qt.Checked)
            self.aov_list_widget.addItem(item)

    def edit_aov(self, item:QListWidgetItem):
        if item.checkState() == Qt.CheckState.Checked:
            item.driver.message >> item.aov.attr(f"outputs[{get_free_driver_index(item.aov)}]").driver
        else:
            print("removing driver")
            item.driver.message // get_aov_attr_for_driver(item.aov, item.driver)
            


@bind_to_host
class OutputDriverManager(QMainWindow):
    def __init__(self, host, parent):
        super().__init__(parent)
        self.setWindowTitle("Screw Drivers")
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
        
        label = QLabel("Drivers (EXR only):")
        label.setStyleSheet("QLabel {font-weight: bold;}")
        vbox.addWidget(label)
        vbox.addWidget(self.driver_list_widget)
        vbox.addWidget(QHLine())
        label = QLabel("Driver Settings:")
        label.setStyleSheet("QLabel {font-weight: bold;}")
        vbox.addWidget(label)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.driver_settings_widget)
        vbox.addWidget(QHLine())
        label = QLabel("AOVs for Driver:")
        label.setStyleSheet("QLabel {font-weight: bold;}")
        vbox.addWidget(label)
        vbox.addWidget(self.aov_list_widget)
            
        cw = QWidget()
        cw.setLayout(vbox)
        self.setCentralWidget(cw)


def main():
    global DEFAULT_RENDER_GLOBALS
    try:
        pc.loadPlugin('mtoa')
    except RuntimeError:
        pc.confirmDialog(message='Arnold Plugin (mtoa) could not be loaded.')
        return
    try:
        DEFAULT_RENDER_GLOBALS = pc.PyNode("defaultArnoldDriver")
    except MayaNodeError:
        import mtoa.core
        mtoa.core.createOptions()
        DEFAULT_RENDER_GLOBALS = pc.PyNode("defaultRenderGlobals")
    odm = OutputDriverManager()
    
