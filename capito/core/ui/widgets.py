import re
from ast import Call
from functools import partial
from itertools import zip_longest
from pathlib import Path
from typing import Callable, Tuple, Dict

from capito.core.helpers import clamp, get_font_dict, get_font_file, hex_to_rgb_int, hex_to_rgb_float
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()

        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() # + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() # + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()
    

class ColorButton(QPushButton):
    """A simple color swatch PushButton.
    The color can be changed via right click menu.
    The current color is stored in the attribute 'color'."""
    def __init__(self, color:QColor, padding:int=0, menu_actions:dict=None):
        super().__init__()
        self.color = color
        self.padding = padding
        self.menu_actions = menu_actions or {}
        self._set_stylesheet()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            partial(self._context_menu)
        )

    def _set_stylesheet(self):
        self.setStyleSheet(f"QWidget {{margin: 0 {self.padding} {self.padding} 0; font-weight: bold; color: {self._contrast_color()}; background-color: {self.color.name()}}}")

    def color_picker(self):
        color = QColorDialog.getColor(initial=self.color)
        if not color.isValid():
            return
        self.color = color
        self._set_stylesheet()
    
    def _context_menu(self, qpoint):
        menu = QMenu(self)
        menu.setStyleSheet(f"QWidget {{background-color: #666666; color: #ffffff}}")

        change_color_action = QAction("Change Color...")
        change_color_action.triggered.connect(self.color_picker)
        menu.addAction(change_color_action)

        for text, func in self.menu_actions.items():
            action = QAction(text)
            action.triggered.connect(partial(func, self))
            menu.addAction(action)

        menu.exec_(QCursor.pos())

    def _contrast_color(self):
        col = "#ffffff"
        rgb = self.color.getRgbF()
        avg = sum(rgb) / 3
        if avg > 0.4:
            col = "#000000"
        return col


class ColorList(QWidget):
    """A color swatch list in a flow layout.
    The color list has to contain hex-colors (eg. #ffffff) as strings.
    On click the callback_func will be called and given the clicked widget
    and optional additional callback_kwargs.
    The callback_func can get the color by accessing the color attribute of the given widget.
    """
    def __init__(self, colors: list[str | list | QColor], callback_func: callable, callback_kwargs: dict=None, padding=0, button_width:str=None):
        super().__init__()
        self.colors = self.init_colors(colors)
        self.callback = callback_func
        if callback_kwargs is None:
            callback_kwargs = {}
        self.callback_kwargs = callback_kwargs
        self.padding = padding
        self.button_width = button_width
        self.color_buttons = []
        self.marked_button = None
        self._create_layout()

    def init_colors(self, colors:list[str | list | QColor]):
        qcolor_list = []
        for color in colors:
            if isinstance(color, str) and color.startswith("#"):
                qcolor_list.append(QColor(color))
            elif isinstance(color, list) and 3 <= len(color) <= 4:
                c = QColor()
                c.setRgbF(*color)
                qcolor_list.append(c)
            elif isinstance(color, QColor):
                qcolor_list.append(color)
            else:
                raise ValueError("Parameter colorlist must contain str, list or QColor (#ffffff, [1,1,1], QColor()).")
        return qcolor_list
                
    def _create_layout(self):
        flow = FlowLayout()
        for color in self.colors:
            btn = ColorButton(color, padding=self.padding, menu_actions={"Set as Standard": self.mark_btn})
            if self.button_width:
                btn.setMinimumWidth(self.button_width)
                btn.setMaximumWidth(self.button_width)
            btn.clicked.connect(partial(self.callback, btn, **self.callback_kwargs))
            flow.addWidget(btn)
            self.color_buttons.append(btn)
        self.setLayout(flow)

    def get_colors(self):
        return [btn.color for btn in self.color_buttons]
    
    def mark_btn(self, button):
        for btn in self.color_buttons:
            btn.setText("")
        button.setText("✓")
        self.marked_button = button


class HeadlineFont(QFont):
    def __init__(self, size=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBold(True)
        self.setPointSize(size)


class IterableListWidget(QListWidget):
    def iterAllItems(self) -> QListWidgetItem:  # pylint: disable=invalid-name
        """Iterate over all items in list."""
        for i in range(self.count()):
            yield self.item(i)

    def getIndex(  # pylint: disable=invalid-name
        self, wanted_item: QListWidgetItem
    ) -> int:
        """Helper method to get the index of a specific item."""
        for i, item in enumerate(self.iterAllItems()):
            if wanted_item == item:
                return i


class MultipleLineDialog(QInputDialog):
    """Ask for mulitple Lines at once."""
    def getMultipleTexts(self, title:str, label:str, placeholders:Tuple[str], texts:Tuple[str]):
        """The longer tuple of placeholders and texts will determine the number of lineedits created.
        The values of 'texts' tuple will be prefilled text in the lineedit.
        """
        self.setWindowTitle(title)
        self.setLabelText(label)
        self.show()
        self.findChild(QLineEdit).hide()
        lineedits = []
        i = 1
        for placeholder, text in zip_longest(placeholders, texts, fillvalue=""):
            lineedit = QLineEdit(text=text)
            lineedit.setPlaceholderText(placeholder)
            self.layout().insertWidget(i, lineedit)
            lineedits.append(lineedit)
            i += 1
        ret = self.exec_() == QDialog.Accepted
        return [lineedit.text() for lineedit in lineedits], ret


class QSplitWidget(QWidget):
    """Test"""

    def __init__(
        self,
        layout1: QLayout,
        layout2: QLayout,
        ratio=(1, 1),
        orientation: Qt.Orientation = Qt.Horizontal,
        remove_margins=True,
    ):
        super().__init__()
        if remove_margins:
            layout1.setContentsMargins(0, 0, 0, 0)
            layout2.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(orientation)
        self.splitter.setHandleWidth(15)
        left_widget = QWidget()
        left_widget.setLayout(layout1)
        right_widget = QWidget()
        right_widget.setLayout(layout2)

        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        width = self.geometry().width()
        self.splitter.setSizes([r * width for r in ratio])
        # self.splitter.setStretchFactor(*ratio)
        layout = QGridLayout(self)
        layout.addWidget(self.splitter)
        self.setLayout(layout)


class Signals(QObject):
    fileChosen = Signal(Path)
    fontChosen = Signal(str)
    colorChosen = Signal(str)
    opacityChosen = Signal(float)
    saveClicked = Signal(str)

    def __init__(self):
        super().__init__()


class EditableTextWidget(QWidget):
    """Widget to show a locked Text and an edit button.
    If the edit button is pressed, the text will be editable.
    If the save button is pressed, saveClicked(text) will be emitted."""

    def __init__(self, text: str, callback: Callable = None):
        super().__init__()
        self.text = text
        self.signals = Signals()
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.text_box = QTextEdit(self.text)
        self.text_box.setDisabled(True)
        self.text_box.setStyleSheet(
            """
            QTextEdit:disabled {background-color:#000000;color:#cccccc;}
            """
        )
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(80)
        self.cancel_btn.hide()
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setMinimumWidth(80)
        self.save_btn = QPushButton("Save")
        self.save_btn.setMinimumWidth(80)
        self.save_btn.hide()

    def _connect_widgets(self):
        self.edit_btn.clicked.connect(self._switch_to_editmode)
        self.cancel_btn.clicked.connect(self._cancel_editmode)
        self.save_btn.clicked.connect(self._save_text)

    def _create_layout(self):
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.text_box)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addStretch()
        hbox.addWidget(self.cancel_btn)
        hbox.addWidget(self.edit_btn)
        hbox.addWidget(self.save_btn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def _switch_to_editmode(self):
        self.text = self.text_box.toPlainText()
        self.text_box.setDisabled(False)
        self.cancel_btn.show()
        self.edit_btn.hide()
        self.save_btn.show()
        self.text_box.setFocus()
        self.text_box.moveCursor(QTextCursor.End)

    def _cancel_editmode(self):
        self.setText(self.text)
        self.text_box.setDisabled(True)
        self.cancel_btn.hide()
        self.edit_btn.show()
        self.save_btn.hide()

    def _save_text(self):
        self.text = self.text_box.toPlainText()
        self.signals.saveClicked.emit(self.text)
        self.text_box.setDisabled(True)
        self.cancel_btn.hide()
        self.edit_btn.show()
        self.save_btn.hide()

    def setText(self, text: str):
        """Set the text of text_box."""
        self.text_box.setPlainText(text)


class RichListItem(QListWidgetItem):
    """A QListWidgetItem that uses whatever widget is handed for Presentation."""

    def __init__(self, widget: QWidget, parent):
        super().__init__(parent)
        self.widget = widget
        self.setSizeHint(self.widget.minimumSizeHint())
        parent.setItemWidget(self, self.widget)


class QFileChooserButton(QWidget):
    def __init__(
        self,
        start_file: Path = None,
        label_text: str = "File: ",
        button_text: str = "...",
        file_filter: str = "JSON (*.json)",
        file_must_exist: bool = True,
        widths=(100, 0, 0),
        placeholder_text: str = "",
    ):
        super().__init__()
        self.file_must_exist = file_must_exist
        self.signals = Signals()
        hbox = QHBoxLayout()
        self.placeholder_text = placeholder_text
        self.file_filter = file_filter
        label = QLabel(label_text)
        if widths[0]:
            label.setMinimumWidth(widths[0])

        self.lineedit = QLineEdit()
        self.lineedit.setPlaceholderText(placeholder_text)
        if start_file is not None:
            self.lineedit.setText(str(start_file))
        if widths[1]:
            self.lineedit.setMinimumWidth(widths[1])

        btn = QPushButton(button_text)
        if widths[2]:
            btn.setMinimumWidth(widths[2])
        btn.clicked.connect(self.open_dialog)

        hbox.addWidget(label)
        hbox.addWidget(self.lineedit)
        hbox.addWidget(btn)
        hbox.setMargin(0)
        self.setLayout(hbox)

    def open_dialog(self):
        if self.file_must_exist:
            filename = QFileDialog.getOpenFileName(
                self, self.placeholder_text, filter=self.file_filter
            )
        else:
            filename = QFileDialog.getSaveFileName(
                self, self.placeholder_text, filter=self.file_filter
            )
        if not filename[0]:
            return
        self.lineedit.setText(str(Path(filename[0])))
        self.signals.fileChosen.emit(Path(filename[0]))


class QIntSliderGroup(QWidget):
    def __init__(
        self,
        label_text="Percent: ",
        min_value: int = 0,
        max_value: int = 100,
        value: int = None,
        widths=(0, 50, 0),
        max_width=None,
    ):
        super().__init__()
        if not value:
            value = int((max_value - min_value) / 2)
        self.min_value = min_value
        self.max_value = max_value

        if max_width:
            self.setMaximumWidth(max_width)

        hbox = QHBoxLayout()
        label = QLabel(label_text)
        if widths[0]:
            label.setMaximumWidth(widths[0])
        hbox.addWidget(label)
        self.lineedit = QLineEdit(str(value))
        self.lineedit.setMaximumWidth(50)
        self.lineedit.setValidator(QIntValidator())
        if widths[1]:
            self.lineedit.setMaximumWidth(widths[1])
            self.lineedit.setMinimumWidth(widths[1])
        hbox.addWidget(self.lineedit)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimumWidth(50)
        self.slider.setMinimum(min_value)
        self.slider.setMaximum(max_value)
        self.slider.setValue(value)
        if widths[2]:
            self.slider.setMaximumWidth(widths[2])
            self.slider.setMinimumWidth(widths[2])
        hbox.addWidget(self.slider)

        self.slider.sliderMoved.connect(self.setLineedit)
        self.lineedit.textEdited.connect(self.setSlider)

        self.setLayout(hbox)

    def setLineedit(self, val: int):
        self.lineedit.setText(str(val))

    def setSlider(self, val: str):
        val = 0 if not val else clamp(int(val), self.min_value, self.max_value)
        self.lineedit.setText(str(val))
        self.slider.setValue(val)

    def get_value(self):
        return self.slider.value()

    def set_value(self, value):
        self.setSlider(value)


class QColorButtonWidget(QWidget):
    def __init__(
        self, label="Color", min_width=30, max_width=30, hex_color=None, label_width=0
    ):
        super().__init__()
        if hex_color is None:
            hex_color = "#000000"
        self.color = QColor(*hex_to_rgb_int(hex_color))
        self.setStyleSheet(
            f"QPushButton#fontcolorbutton {{background-color: {self.get_hex()};}}"
        )
        hbox = QHBoxLayout()
        hbox.setMargin(0)
        if label:
            label_widget = QLabel(label)
            if not label_width:
                label_width = label_widget.sizeHint().width()

            label_widget.setMinimumWidth(label_widget.sizeHint().width())
            label_widget.setMaximumWidth(label_widget.sizeHint().width())
            hbox.addWidget(label_widget)
        self.color_button = QPushButton("")
        self.color_button.setObjectName("fontcolorbutton")
        self.color_button.setMinimumWidth(min_width)
        self.color_button.setMaximumWidth(max_width)
        hbox.addWidget(self.color_button)
        self.color_button.clicked.connect(self.select_color)

        self.setMinimumWidth(label_width + max_width + 10)
        self.setMaximumWidth(label_width + max_width + 10)
        self.setLayout(hbox)

    def select_color(self):
        self.color = QColorDialog.getColor()
        self.setStyleSheet(
            f"QPushButton#fontcolorbutton {{background-color: {self.get_hex()};}}"
        )

    def get_color(self):
        return self.color

    def get_hex(self):
        return self.color.name()


class QFontTypeChooserWidget(QWidget):
    def __init__(self, font_dir: Path = None, font_tuple: Tuple[str, str] = None):
        super().__init__()
        if font_tuple is None:
            font_tuple = ("NotoSansMono_Condensed", "Regular")
        self.font_dir = font_dir
        self.font_dict = get_font_dict(font_dir)

        hbox = QHBoxLayout()
        hbox.setMargin(0)
        self.font_combo = QComboBox()
        self.style_combo = QComboBox()
        for font, styles in self.font_dict.items():
            self.font_combo.addItem(font)
            for style in styles:
                self.style_combo.addItem(style)

        self.font_combo.setCurrentText(font_tuple[0])
        self.style_combo.setCurrentText(font_tuple[1])
        hbox.addWidget(self.font_combo)
        hbox.addWidget(self.style_combo)

        self.font_combo.currentTextChanged.connect(self.font_combo_changed)

        self.setLayout(hbox)

    def font_combo_changed(self, font):
        self.style_combo.clear()
        for style in self.font_dict[font]:
            self.style_combo.addItem(style)
        if "Regular" in self.font_dict[font]:
            self.style_combo.setCurrentText("Regular")

    def get_font_file(self) -> Path:
        return get_font_file(
            self.font_dir, self.font_combo.currentText(), self.style_combo.currentText()
        )

    def get_font_tuple(self) -> Tuple[str, str]:
        return (self.font_combo.currentText(), self.style_combo.currentText())


class QFfmpegFontChooser(QWidget):
    def __init__(
        self,
        font_folder: Path,
        hex_color: str = None,
        opacity=100,
        font_tuple: Tuple[str, str] = None,
        size=18,
    ):
        super().__init__()
        hbox = QHBoxLayout()
        hbox.setMargin(0)
        self.font_color_button = QColorButtonWidget(hex_color=hex_color)
        hbox.addWidget(self.font_color_button)
        self.fontopacity_slider = QIntSliderGroup(
            label_text="Opacity", widths=(50, 30, 100), max_width=200, value=opacity
        )
        hbox.addWidget(self.fontopacity_slider)
        self.font_chooser = QFontTypeChooserWidget(font_folder, font_tuple)
        hbox.addWidget(self.font_chooser)
        size_label = QLabel("Size")
        size_label.setMaximumWidth(30)
        hbox.addWidget(size_label)
        self.fontsize_spinbox = QSpinBox()
        self.fontsize_spinbox.setValue(size)
        self.fontsize_spinbox.setMinimumWidth(50)
        self.fontsize_spinbox.setMaximumWidth(50)
        hbox.addWidget(self.fontsize_spinbox)
        self.setLayout(hbox)

    def get_color(self):
        return self.font_color_button.get_color()

    def get_hex(self):
        return self.font_color_button.get_hex()

    def get_opacity(self):
        return self.fontopacity_slider.get_value()

    def get_font_file(self):
        return self.font_chooser.get_font_file()

    def get_font_tuple(self):
        return self.font_chooser.get_font_tuple()

    def get_size(self):
        return self.fontsize_spinbox.value()


class QHLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class QHeadingLine(QWidget):
    def __init__(self, text, bold=True):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        heading_font = QFont()
        heading_font.setBold(True)

        hbox = QHBoxLayout()
        hbox.setMargin(0)
        hbox.setSpacing(0)
        margin_heading = QLabel("Margins")
        margin_heading.setAlignment(Qt.AlignCenter)
        margin_heading.setMaximumWidth(margin_heading.minimumSizeHint().width())
        margin_heading.setFont(heading_font)
        hbox.addWidget(QHLine())
        hbox.addWidget(margin_heading)
        hbox.addWidget(QHLine())

        self.setLayout(hbox)


class LoadingProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        self.setValue(0)
        self.setTextVisible(False)
        self.__animation = QPropertyAnimation(self, b"loading")
        self.__animation.setStartValue(self.minimum())
        self.__animation.setEndValue(self.maximum())
        self.__animation.valueChanged.connect(self.__loading)
        self.__animation.setDuration(1000)
        self.__animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.__animation.start()

    def __loading(self, v):
        self.setValue(v)
        if self.__animation.currentValue() == self.__animation.endValue():
            self.__animation.setDirection(QAbstractAnimation.Backward)
            self.setInvertedAppearance(True)
            self.__animation.start()
        elif self.__animation.currentValue() == self.__animation.startValue():
            self.__animation.setDirection(QAbstractAnimation.Forward)
            self.setInvertedAppearance(False)
            self.__animation.start()

    def setAnimationType(self, type: str):
        if type == "fade":
            self.setStyleSheet(
                """
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop: 0.5 #CCCCCC, stop: 0.6 #CCCCCC, stop:1 transparent);
                }
            """
            )
            self.__animation.setEasingCurve(QEasingCurve.Linear)
            self.__animation.setDuration(500)
        elif type == "dynamic":
            self.setStyleSheet("")
            self.__animation.setEasingCurve(QEasingCurve.InOutQuad)
            self.__animation.setDuration(1000)


class OutputConsole(QTextEdit):
    """Colored text output console.
    Example
    -------
    from cmt.ui.widgets.outputconsole import OutputConsole
    widget = OutputConsole()
    widget.add_color("^Error", 217, 83, 79)
    widget.add_color("^Fail", 240, 173, 78)
    widget.add_color("^Success", 92, 184, 92)
    widget.show()
    widget.write("And now some text\n")
    widget.write("ERROR: This is an error\n")
    widget.write("FAIL: We have failed\n")
    widget.write("SUCCESS: We did it!\n")
    """

    normal_color = QColor(200, 200, 200)

    def __init__(self, parent=None):
        """Constructor

        :param parent: Parent QWidget.
        """
        super(OutputConsole, self).__init__(parent)
        self.setReadOnly(True)
        self.color_regex = {}
        self.setTextColor(OutputConsole.normal_color)

    def add_color(self, regex, r, g, b):
        """Add a regex with associated color.

        :param regex: Regular expression pattern
        :param r: Red 0-255
        :param g: Green 0-255
        :param b: Blue 0-255
        """
        regex = re.compile(regex, re.IGNORECASE)
        self.color_regex[regex] = QColor(r, g, b)

    def write(self, text):
        """Write text into the QTextEdit."""
        # Color the output if it matches any regex
        for regex, color in self.color_regex.items():
            if regex.search(text):
                self.setTextColor(color)
                break
        self.insertPlainText(text)
        self.setTextColor(OutputConsole.normal_color)

    def flush(self):
        """Required for stream purposes"""
        pass
