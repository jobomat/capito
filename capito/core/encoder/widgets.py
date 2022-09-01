from pathlib import Path
from subprocess import TimeoutExpired
import time, threading, os

from plumbum import BG
from PySide2.QtGui import QColor, QFont, QIcon, QColor, QPalette, Qt  # pylint:disable=wrong-import-order
from PySide2.QtCore import Signal, QObject
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget
)
from capito.core.ui.widgets import (
    QFileChooserButton,
    QIntSliderGroup,
    QHLine,
    LoadingProgressBar,
    QFfmpegFontChooser
)
from capito.core.encoder.util import guess_sequence_pattern
from capito.core.helpers import remap_value
from capito.core.ui.decorators import bind_to_host


class Signals(QObject):
    fileChosen = Signal(Path)
    def __init__(self):
        super().__init__()


@bind_to_host
class DrawTextSettings(QWidget):
    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setStyleSheet(r"QGroupBox {font-weight: bold;}")
        font_folder = Path(os.environ.get("CAPITO_BASE_DIR"), "resources", "fonts")

        vbox = QVBoxLayout()
        vbox.setSpacing(5)
        vbox.setMargin(5)
        
        margin_hbox = QHBoxLayout()
        margin_groupbox = QGroupBox()
        margin_groupbox.setLayout(margin_hbox)
        margin_groupbox.setTitle("Margins")
        self.margin_widgets = {}
        for direction in ["Top", "Right", "Bottom", "Left"]:
            margin_label = QLabel(direction)
            margin_label.setMaximumWidth(50)
            margin_hbox.addWidget(QLabel(direction))
            self.margin_widgets[direction] = QSpinBox()
            self.margin_widgets[direction].setMinimumWidth(60)
            self.margin_widgets[direction].setMaximumWidth(60)
            margin_hbox.addWidget(self.margin_widgets[direction])
        margin_hbox.addStretch()

        font_vbox = QVBoxLayout()
        font_groupbox = QGroupBox()
        font_groupbox.setLayout(font_vbox)
        font_groupbox.setTitle("Font")
        self.font_widget = QFfmpegFontChooser(font_folder)
        font_vbox.addWidget(self.font_widget)
        
        vbox.addWidget(margin_groupbox)
        vbox.addWidget(font_groupbox)
        vbox.addStretch()
        self.setLayout(vbox)
        self.show()


class InputWidget(QWidget):
    def __init__(self, widths):
        super().__init__()
        self.start_num = None
        self.chosen_image:Path = None
        
        vbox = QVBoxLayout()
        vbox.setMargin(0)

        # Create Widgets and Layouts
        self.input_file_chooser = QFileChooserButton(
            label_text="Input Sequence", file_filter="", widths=widths,
            placeholder_text="Select the first frame of the image sequence."
        )
        start_label = QLabel("Encode from")
        start_label.setMinimumWidth(widths[0])
        self.start_frame_spinbox = QSpinBox()
        self.start_frame_spinbox.setMinimumWidth(widths[0])
        end_label = QLabel("Encode to")
        self.end_frame_spinbox = QSpinBox()
        self.end_frame_spinbox.setMinimumWidth(widths[0])
        self.frame_number_label = QLabel("")
        self.frame_pattern_label = QLabel("No image selected.")
        # second line
        hbox = QHBoxLayout()
        hbox.addWidget(start_label)
        hbox.addWidget(self.start_frame_spinbox)
        hbox.addWidget(end_label)
        hbox.addWidget(self.end_frame_spinbox)
        hbox.addStretch()
        hbox.addWidget(self.frame_number_label)
        hbox.addWidget(self.frame_pattern_label)
        
        # Connect
        self.input_file_chooser.signals.fileChosen.connect(self.process_file)
        self.start_frame_spinbox.valueChanged.connect(self.end_frame_spinbox.setMinimum)
        self.end_frame_spinbox.valueChanged.connect(self.start_frame_spinbox.setMaximum)
        self.start_frame_spinbox.valueChanged.connect(self.update_frame_number_label)
        self.end_frame_spinbox.valueChanged.connect(self.update_frame_number_label)

        
        # Add
        vbox.addWidget(self.input_file_chooser)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
    
    def process_file(self, file_path:Path):
        self.chosen_image = file_path
        self.input_file_chooser.lineedit.setText(str(file_path))
        result = guess_sequence_pattern(file_path)
        if result is None:
            return
        (self.ffmpeg_pattern, glob_pattern, self.start_num) = result
        self.start_frame_spinbox.setMinimum(self.start_num)
        self.start_frame_spinbox.setValue(self.start_num)
        folder = file_path.parent
        all_files = list(folder.glob(glob_pattern))
        num_files = len(all_files)
        self.end_num = self.start_num + num_files
        self.end_frame_spinbox.setMaximum(self.end_num)
        self.end_frame_spinbox.setValue(self.end_num)
        self.frame_pattern_label.setText(f" |  {self.ffmpeg_pattern.name}")

    def update_frame_number_label(self):
        self.frame_number_label.setText(f"{self.get_number_of_frames()} frames")

    def get_start_frame(self):
        return self.start_frame_spinbox.value()

    def get_end_frame(self):
        return self.end_frame_spinbox.value()

    def get_number_of_frames(self):
        return self.end_frame_spinbox.value() - self.start_frame_spinbox.value()

    def get_ffmpeg_pattern(self):
        return str(self.ffmpeg_pattern)


class OptionsWidget(QWidget):
    def __init__(self, widths):
        super().__init__()

        hbox = QHBoxLayout()
        hbox.setMargin(0)
        fps_label = QLabel("Framerate FPS")
        fps_label.setMinimumWidth(widths[0])
        hbox.addWidget(fps_label)
        self.framerate_spinbox = QSpinBox()
        self.framerate_spinbox.setValue(24)
        self.framerate_spinbox.setMinimumWidth(widths[0])
        hbox.addWidget(self.framerate_spinbox)
        self.quality_slider = QIntSliderGroup(label_text="Quality", widths=(widths[0], widths[0], 0))
        hbox.addWidget(self.quality_slider)
        
        self.setLayout(hbox)

    def get_framerate(self):
        return self.framerate_spinbox.value()
        
    def get_quality(self):
        return remap_value(0, 100, 30, 16, self.quality_slider.getValue())





class MainWidget(QWidget):
    """QWidget containing FFMpeg Options."""

    def __init__(self, ffmpeg, parent=None):
        super().__init__(parent)
        self.ffmpeg = ffmpeg
        widths = (80, 0, 50)
        
        vbox = QVBoxLayout()
        vbox.setMargin(0)

        self.input_widget = InputWidget(widths)
        vbox.addWidget(self.input_widget)

        vbox.addWidget(QHLine())

        self.options_widget = OptionsWidget(widths)
        vbox.addWidget(self.options_widget)
        
        self.output_file_chooser = QFileChooserButton(
            label_text="Output MP4", file_must_exist=False, file_filter="*.mp4", widths=widths,
            placeholder_text="Select the location and filename for the mp4."
        )
        vbox.addWidget(self.output_file_chooser)

        vbox.addStretch()

        vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        self.status_text = QLabel()
        hbox.addWidget(self.status_text)
        self.progress_bar = LoadingProgressBar()
        self.progress_bar.hide()
        hbox.addWidget(self.progress_bar)
        hbox.addStretch()
        self.encode_button = QPushButton("Encode")
        self.encode_button.clicked.connect(self.encode)
        hbox.addWidget(self.encode_button)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def encode(self):
        parameters = [
            "-framerate", self.options_widget.get_framerate(),
            "-start_number", self.input_widget.get_start_frame(),
            "-i", self.input_widget.get_ffmpeg_pattern(),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-y", #Overwrite if existing
            "-crf", self.options_widget.get_quality(),
            # "-vf", self.drawtext_widget.get_drawtext(),
            "-t", self.input_widget.get_number_of_frames() / self.options_widget.get_framerate(),
            self.output_file_chooser.lineedit.text()
        ]
        print(parameters)
        self.status_text.setText(f"Encoding")
        self.progress_bar.show()
        self.process = self.ffmpeg.popen(parameters)
        try:
            self.process.communicate(timeout=1)
        except TimeoutExpired:
            pass

        self.update_thread = threading.Thread(target=self.check_process, daemon=True)
        self.update_thread.start()

    def check_process(self):
        while self.process.poll() is None:
            time.sleep(1)
        self.status_text.setText(f"Encoding finished!")
        self.progress_bar.hide()



class ErrorWidget(QWidget):
    """QWidget containing Error Message and Instructions.
    This is only used in case ffmpeg was not found via env vars."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        lines = QVBoxLayout()
        lines.addWidget(QLabel("Sorry but ffmpeg.exe could not be detected!"))
        lines.addWidget(QLabel("For SequenceEncoder to work you need to:"))
        lines.addWidget(QLabel("   - install ffmpeg"))
        lines.addWidget(QLabel("   - add environment variable FFMPEG with full path to the ffmpeg executable."))
        lines.addStretch()
        # TODO: Enable user to pick ffmpeg and add the env var from here.
        self.setLayout(lines)
