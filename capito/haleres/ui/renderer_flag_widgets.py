from functools import partial
from typing import Any, List

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from capito.core.ui.decorators import bind_to_host
from capito.haleres.renderer import RendererFlag
from capito.haleres.renderer import Renderer
from capito.haleres.ui.utils import clear_layout, SIGNALS


INT_OR_EMPTY_REGEXP = QRegExp('(^[0-9]+$|^$)')
INT_OR_EMPTY_VALIDATOR = QRegExpValidator(INT_OR_EMPTY_REGEXP)


class RendererFlagEditWidget(QWidget):
    def __init__(self, flag:RendererFlag, parent=None):
        super().__init__(parent)
        self.flag = flag
        if self.flag.type == "str":
            lineedit = QLineEdit()
            if self.flag.value:
                lineedit.setText(self.flag.value)
            lineedit.textChanged.connect(flag.set_value)
            self.widget = lineedit
        elif self.flag.type == "int":
            lineedit = QLineEdit()
            lineedit.setValidator(INT_OR_EMPTY_VALIDATOR)
            if self.flag.value:
                lineedit.setText(str(self.flag.value))
            lineedit.textChanged.connect(flag.set_value)
            self.widget = lineedit
        elif self.flag.type == "bool":
            checkbox = QCheckBox("")
            if self.flag.value:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.flag.set_value)
            self.widget = checkbox
        elif self.flag.type == "choice":
            combo = QComboBox()
            for val in self.flag.choices:
                combo.addItem(str(val))
            if self.flag.value:
                combo.setCurrentText(str(self.flag.value))
            combo.currentTextChanged.connect(flag.set_value)
            self.widget = combo
        
        hbox = QHBoxLayout()
        hbox.setMargin(0)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)
        hbox.addWidget(self.widget)
        self.setLayout(hbox)

    def get_value(self):
        if self.flag.type == "str":
            return self.widget.text()
        elif self.flag.type == "int":
            return int(self.widget.text())
        elif self.flag.type == "bool":
            return self.widget.isChecked()
        elif self.flag.type == "choice":
            return self.widget.currentText()


class RendererFlagDisplayList(QWidget):
    """Widget listing all flags of a renderer"""
    def __init__(self):
        super().__init__()
        SIGNALS.renderer_selected.connect(self._renderer_changed)
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        
    def load_flags(self, flags: List[RendererFlag]):
        self.clear_layout()
        num_lines = 0
        for line, flag in enumerate(flags, start=1):
            self.grid_layout.addWidget(QLabel(flag.name), line, 1)
            self.grid_layout.addWidget(RendererFlagEditWidget(flag), line, 2)
            self.grid_layout.setRowStretch(line, 0)
            num_lines = line + 1
        #self.grid_layout.addWidget(QWidget(), num_lines, 1)
        self.grid_layout.setRowStretch(num_lines, 1)
        
    def clear_layout(self):
        clear_layout(self.grid_layout)
    
    def _renderer_changed(self, renderer:Renderer):
        self.clear_layout()
        if renderer is not None:
            self.load_flags(renderer.get_editable_flags())


@bind_to_host
class TestWindow(QMainWindow):
    def __init__(self, renderer, host: str=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TEST")
        vbox = QVBoxLayout()
        self.renderer = renderer

        rfdl = RendererFlagDisplayList(self.renderer.get_editable_flags())
        vbox.addWidget(rfdl)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)
