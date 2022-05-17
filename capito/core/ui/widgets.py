import re

from PySide2.QtGui import Qt, QColor
from PySide2.QtWidgets import (
    QGridLayout,
    QLayout,
    QSplitter,
    QWidget,
    QFrame,
    QTextEdit
)


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


class QHLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


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
