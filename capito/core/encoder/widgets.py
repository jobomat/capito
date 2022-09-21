"""Module with the ui components of the encoder"""
import os
import threading
import time
from functools import partial
from pathlib import Path
from subprocess import TimeoutExpired

from capito.core.encoder.util import guess_sequence_pattern
from capito.core.file.utils import sanitize_name
from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import (
    LoadingProgressBar,
    QColorButtonWidget,
    QFfmpegFontChooser,
    QFileChooserButton,
    QHLine,
    QIntSliderGroup,
)
from PySide2.QtCore import QObject, Signal
from PySide2.QtGui import QColor  # pylint:disable=wrong-import-order
from PySide2.QtGui import QCursor, QFont, QIcon, QPalette, Qt
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QAbstractItemView,
    QAction,
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
    QMenu,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class Signals(QObject):
    """Special Signals for communicating between custom Widgets"""

    fileChosen = Signal(Path)
    presetChanged = Signal(dict)

    def __init__(self):
        super().__init__()


@bind_to_host
class DrawTextSettings(QMainWindow):
    """Settings window for margins, font and box settings"""

    def __init__(self, host=None, parent=None, encoder_win=None):
        super().__init__(parent)
        self.encoder_win = encoder_win
        self.encoder_win.signals.closed.connect(self.close)
        self.encoder = encoder_win.encoder

        self.setWindowTitle("Burn In Settings")
        self.settings = self.encoder.get_current_settings()

        self.setMinimumSize(360, 200)
        self.setStyleSheet(r"QGroupBox {font-weight: bold;}")
        self.font_folder = Path(os.environ.get("CAPITO_BASE_DIR"), "resources", "fonts")

        vbox = QVBoxLayout()
        vbox.setSpacing(5)
        vbox.setMargin(5)

        margin_hbox = QHBoxLayout()
        margin_groupbox = QGroupBox()
        margin_groupbox.setLayout(margin_hbox)
        margin_groupbox.setTitle("Screen Margin")
        self.margin_widgets = {}
        for direction in self.settings["burnin_defaults"]["margins"]:
            margin_label = QLabel(direction.capitalize())
            margin_label.setMaximumWidth(50)
            margin_hbox.addWidget(QLabel(direction))
            spinbox = QSpinBox()
            spinbox.setMinimumWidth(60)
            spinbox.setMaximumWidth(60)
            spinbox.setValue(self.settings["burnin_defaults"]["margins"][direction])
            self.margin_widgets[direction] = spinbox
            margin_hbox.addWidget(self.margin_widgets[direction])
        margin_hbox.addStretch()

        font_vbox = QVBoxLayout()
        font_groupbox = QGroupBox()
        font_groupbox.setLayout(font_vbox)
        font_groupbox.setTitle("Font")
        self.font_widget = QFfmpegFontChooser(
            self.font_folder,
            hex_color=self.settings["burnin_defaults"]["font_color"],
            opacity=self.settings["burnin_defaults"]["font_opacity"],
            font_tuple=self.settings["burnin_defaults"]["font_tuple"],
            size=self.settings["burnin_defaults"]["font_size"],
        )
        font_vbox.addWidget(self.font_widget)

        box_hbox = QHBoxLayout()
        box_groupbox = QGroupBox()
        box_groupbox.setLayout(box_hbox)
        box_groupbox.setTitle("Background Box (Font)")
        self.box_color_button = QColorButtonWidget(
            hex_color=self.settings["burnin_defaults"]["box_color"]
        )
        box_hbox.addWidget(self.box_color_button)
        self.box_opacity_widget = QIntSliderGroup(
            label_text="Opacity",
            value=self.settings["burnin_defaults"]["box_opacity"],
            widths=(50, 30, 100),
            max_width=200,
        )
        box_hbox.addWidget(self.box_opacity_widget)
        box_hbox.addWidget(QLabel("Padding"))
        self.box_padding_widget = QSpinBox()
        self.box_padding_widget.setMaximumWidth(60)
        self.box_padding_widget.setMinimumWidth(60)
        self.box_padding_widget.setValue(
            self.settings["burnin_defaults"]["box_padding"]
        )
        box_hbox.addWidget(self.box_padding_widget)
        box_hbox.addStretch()

        button_hbox = QHBoxLayout()
        button_hbox.addStretch()
        ok_button = QPushButton("OK")
        ok_button.setMinimumWidth(100)
        ok_button.clicked.connect(self.ok_clicked)
        button_hbox.addWidget(ok_button)

        vbox.addWidget(margin_groupbox)
        vbox.addWidget(font_groupbox)
        vbox.addWidget(box_groupbox)
        vbox.addStretch()
        vbox.addLayout(button_hbox)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)
        # self.setLayout(vbox)
        # self.show()

    def ok_clicked(self):
        """Called if user clicked ok"""
        self.encoder.burnin_defaults = self.get_values()
        self.close()

    def get_values(self):
        """Assemble the settings in a dict."""
        margins_dict = {}
        for direction in self.settings["burnin_defaults"]["margins"]:
            margins_dict[direction] = self.margin_widgets[direction].value()
        return {
            "margins": margins_dict,
            "font_color": self.font_widget.get_hex(),
            "font_opacity": self.font_widget.get_opacity(),
            "font_tuple": self.font_widget.get_font_tuple(),
            "font_size": self.font_widget.get_size(),
            "box_color": self.box_color_button.get_hex(),
            "box_opacity": self.box_opacity_widget.get_value(),
            "box_padding": self.box_padding_widget.value(),
        }


class InputWidget(QWidget):
    """The Input section of the ui"""

    def __init__(self, widths):
        super().__init__()
        self.start_num = None
        self.chosen_image: Path = None

        vbox = QVBoxLayout()
        vbox.setMargin(0)

        # Create Widgets and Layouts
        self.input_file_chooser = QFileChooserButton(
            label_text="Input Sequence",
            file_filter="",
            widths=widths,
            button_text="Choose Sequence...",
            placeholder_text="Select the first frame of the image sequence.",
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

    def process_file(self, file_path: Path):
        """Get the necessary infos out of the chosen file.
        eg startframe, endframe, ffmpeg-framepattern..."""
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
        """Update the QLabel for the frame number."""
        self.frame_number_label.setText(f"{self.get_number_of_frames()} frames")

    def get_start_frame(self):
        """get strat frame"""
        return self.start_frame_spinbox.value()

    def get_end_frame(self):
        """get end frame"""
        return self.end_frame_spinbox.value()

    def get_number_of_frames(self):
        """convenience method calculting the sequence length"""
        return self.end_frame_spinbox.value() - self.start_frame_spinbox.value()

    def get_ffmpeg_pattern(self):
        """just return the pattern."""
        return str(self.ffmpeg_pattern)


class OptionsWidget(QWidget):
    """The custom widget for the options-section (quality and framerate)"""

    def __init__(self, widths, change_signal):
        super().__init__()

        change_signal.connect(self.load_settings)

        hbox = QHBoxLayout()
        hbox.setMargin(0)
        fps_label = QLabel("Framerate FPS")
        fps_label.setMinimumWidth(widths[0])
        hbox.addWidget(fps_label)
        self.framerate_spinbox = QSpinBox()

        self.framerate_spinbox.setMinimumWidth(widths[0])
        hbox.addWidget(self.framerate_spinbox)
        self.quality_slider = QIntSliderGroup(
            label_text="Quality", widths=(widths[0], widths[0], 0)
        )
        hbox.addWidget(self.quality_slider)

        self.setLayout(hbox)

    def load_settings(self, settings):
        """Method called by a signal if something changed"""
        self.framerate_spinbox.setValue(settings["framerate"])
        self.quality_slider.set_value(settings["quality"])

    def get_framerate(self):
        """get the framerate"""
        return self.framerate_spinbox.value()

    def get_quality(self):
        """get the quality"""
        return self.quality_slider.get_value()


class DrawtextWidget(QWidget):
    """The custom grid based drawtext widget."""

    def __init__(self, change_signal):
        super().__init__()
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(5)
        self.grid.setVerticalSpacing(2)
        self.text_edits = {}
        self.create_grid()
        change_signal.connect(self.fill_grid)
        self.setLayout(self.grid)

    def create_grid(self):
        """Create a 3*2 grid"""
        for i, vertical in enumerate(["top", "bottom"]):
            for j, horizontal in enumerate(["left", "center", "right"]):
                hbox = QHBoxLayout()

                text_edit = QTextEdit()
                text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
                text_edit.customContextMenuRequested.connect(
                    partial(self.context_menu, text_edit)
                )

                self.text_edits[f"{vertical}_{horizontal}"] = text_edit

                hbox.addWidget(text_edit)
                groupbox = QGroupBox()
                groupbox.setTitle(f"{vertical.capitalize()} {horizontal.capitalize()}")
                groupbox.setLayout(hbox)
                self.grid.addWidget(groupbox, i, j)

    def fill_grid(self, settings):
        """Method called by a signal if settings changed (preset selected)"""
        for pos, burnin in settings["burnins"].items():
            self.text_edits[pos].setText(burnin)

    def context_menu(self, text_edit, *args):
        """Create the context menu for Burnin placeholders."""
        menu = QMenu(self)

        action1 = QAction("Frame number (<FRAME:padding=INT:start=INT>)")
        action1.triggered.connect(partial(self.insert_text, text_edit, "<FRAME>"))
        menu.addAction(action1)

        action2 = QAction("Datetime (<DATETIME:format=strftime-formatstring>)")
        action2.triggered.connect(partial(self.insert_text, text_edit, "<DATETIME>"))
        menu.addAction(action2)

        action3 = QAction("Project Name (<PROJECTNAME>)")
        action3.triggered.connect(partial(self.insert_text, text_edit, "<PROJECTNAME>"))
        menu.addAction(action3)

        action4 = QAction("Output filename (<OUTFILE:full_path=BOOL>)")
        action4.triggered.connect(partial(self.insert_text, text_edit, "<OUTFILE>"))
        menu.addAction(action4)

        menu.exec_(QCursor.pos())

    def insert_text(self, text_edit, text):
        """Callback for context menu insertion."""
        cursor = text_edit.textCursor()
        cursor.insertText(text)

    def get_burnins(self):
        """Get burnins as dict"""
        return {k: widget.toPlainText() for k, widget in self.text_edits.items()}


@bind_to_host
class SavePresetWindow(QMainWindow):
    """Dialog to appear for saving presets."""

    def __init__(
        self,
        host=None,
        parent=None,
        encoder=None,
        save_callback=None,
        label: str = "Save for ...",
        preset_name="New Preset",
    ):
        super().__init__(parent)
        self.alias = None
        self.encoder = encoder
        self.save_callback = save_callback
        possibilities = [
            ("user", "... me."),
            ("projectuser", "... me in the current project."),
            ("project", ".. all users in the current project."),
        ]

        vbox = QVBoxLayout()
        self.preset_name_lineedit = QLineEdit()
        self.preset_name_lineedit.setText(preset_name)
        self.preset_name_lineedit.setPlaceholderText("Specify a Preset Name")
        vbox.addWidget(self.preset_name_lineedit)
        vbox.addWidget(QLabel(label))

        for alias, label in possibilities:
            radio = QRadioButton(label)
            vbox.addWidget(radio)
            if alias not in self.encoder._layered_settings.alias.keys():
                radio.setEnabled(False)
            radio.clicked.connect(partial(self.set_alias, alias))

        hbox = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        hbox.addWidget(cancel_btn)
        self.ok_btn = QPushButton("Save")
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.save)
        hbox.addWidget(self.ok_btn)

        vbox.addLayout(hbox)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def set_alias(self, alias):
        """Set alias and enable the ok button."""
        self.alias = alias
        self.ok_btn.setEnabled(True)

    def save(self):
        """Save the preset"""
        name = self.preset_name_lineedit.text()
        self.encoder._layered_settings.set(
            self.alias, f"PRESET:{name}", self.encoder.get_current_settings()
        )
        self.encoder._layered_settings.save(self.alias)
        self.save_callback(name)
        self.close()


class MainWidget(QWidget):
    """QWidget containing FFMpeg Options."""

    def __init__(self, parent):
        super().__init__()
        self.encoder_win = parent
        self.encoder = parent.encoder
        widths = (80, 0, 120)

        self.signals = Signals()

        vbox = QVBoxLayout()
        vbox.setMargin(0)

        self.input_widget = InputWidget(widths)
        vbox.addWidget(self.input_widget, stretch=0)

        vbox.addWidget(QHLine())

        settings_hbox = QHBoxLayout()
        settings_label = QLabel("Presets")
        settings_label.setMinimumWidth(widths[0])
        settings_hbox.addWidget(settings_label)
        self.settings_preset_combobox = QComboBox()
        self.settings_preset_combobox.currentTextChanged.connect(self.preset_changed)
        settings_hbox.addWidget(self.settings_preset_combobox)
        settings_hbox.addStretch()
        save_btn = QPushButton("Save Preset...")
        save_btn.setMinimumWidth(widths[2])
        save_btn.clicked.connect(self.save_preset)
        settings_hbox.addWidget(save_btn)
        # save_as_btn = QPushButton("Save Preset as...")
        # save_as_btn.setMinimumWidth(widths[2])
        # settings_hbox.addWidget(save_as_btn)
        vbox.addLayout(settings_hbox)

        vbox.addWidget(QHLine())

        self.options_widget = OptionsWidget(widths, self.signals.presetChanged)
        vbox.addWidget(self.options_widget, stretch=0)

        vbox.addWidget(QHLine())

        burnin_hbox = QHBoxLayout()
        burnin_hbox.addWidget(QLabel("Burn Ins"))
        burnin_hbox.addStretch()
        drawtext_settings_button = QPushButton("Burn In Settings...")
        drawtext_settings_button.setMinimumWidth(widths[2])
        drawtext_settings_button.clicked.connect(self.open_drawtext_settings)
        burnin_hbox.addWidget(drawtext_settings_button)
        vbox.addLayout(burnin_hbox)

        self.drawtext_widget = DrawtextWidget(self.signals.presetChanged)
        vbox.addWidget(self.drawtext_widget, stretch=1)

        vbox.addWidget(QHLine())

        self.output_file_chooser = QFileChooserButton(
            label_text="Output MP4",
            file_must_exist=False,
            file_filter="*.mp4",
            widths=widths,
            button_text="Save as ...",
            placeholder_text="Select the location and filename for the mp4.",
        )
        vbox.addWidget(self.output_file_chooser, stretch=0)

        vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        self.status_text = QLabel()
        hbox.addWidget(self.status_text)
        self.progress_bar = LoadingProgressBar()
        self.progress_bar.hide()
        hbox.addWidget(self.progress_bar)
        hbox.addStretch()
        self.show_command_button = QPushButton("Show Command")
        self.show_command_button.clicked.connect(self.show_command)
        hbox.addWidget(self.show_command_button)
        self.encode_button = QPushButton("Encode")
        self.encode_button.setMinimumWidth(widths[2])
        self.encode_button.clicked.connect(self.encode)
        hbox.addWidget(self.encode_button)
        vbox.addLayout(hbox)

        self.rebuild_preset_combobox(
            self.encoder._layered_settings["last_selected_preset"]
        )

        self.setLayout(vbox)

    def rebuild_preset_combobox(self, select_preset=None):
        """Rebuild the preset dropdown."""
        self.settings_preset_combobox.clear()
        for preset in self.encoder.get_availible_presets():
            self.settings_preset_combobox.addItem(preset)
        if not select_preset:
            select_preset = self.encoder._layered_settings["last_selected_preset"]
        self.settings_preset_combobox.setCurrentText(select_preset)
        self.load_preset(select_preset)

    def preset_changed(self, item_text):
        """Method called when user changes preset dropdown."""
        self.encoder._layered_settings.set("user", "last_selected_preset", item_text)
        self.encoder._layered_settings.save("user")
        self.load_preset(item_text)

    def load_preset(self, item_text):
        """Perform all necessary actions to load a preset."""
        self.encoder.load_preset(item_text)
        self.signals.presetChanged.emit(self.encoder.get_current_settings())

    def save_preset(self):
        """Save the current settings as a new preset."""
        self.set_encoder_settings()
        SavePresetWindow(
            encoder=self.encoder, save_callback=self.rebuild_preset_combobox
        )

    def open_drawtext_settings(self):
        """Open the drawtext settings window."""
        DrawTextSettings(encoder_win=self.encoder_win)

    def encoding_started(self):
        """Serves as a callback for the encoder.encoding_started_callbacks list."""
        self.status_text.setText(f"Encoding")
        self.progress_bar.show()

    def encoding_ended(self, elapsed_seconds):
        """Serves as a callback for the encoder.encoding_ended_callbacks list."""
        self.status_text.setText(f"Encoding finished in {elapsed_seconds} seconds.")
        self.progress_bar.hide()

    def set_encoder_settings(self):
        """Gather all the info from the GUI and set it to the encoder instance."""
        self.encoder.framerate = self.options_widget.get_framerate()
        self.encoder.quality = self.options_widget.get_quality()
        self.encoder.burnins = self.drawtext_widget.get_burnins()
        self.encoder.startframe = self.input_widget.get_start_frame()
        self.encoder.endframe = self.input_widget.get_end_frame()
        self.encoder.input_pattern = self.input_widget.get_ffmpeg_pattern()
        self.encoder.output_file = self.output_file_chooser.lineedit.text()

    def encode(self):
        """Performed when user presses "Encode" Button."""
        self.set_encoder_settings()
        if self.encoding_started not in self.encoder.encoding_started_callbacks:
            self.encoder.encoding_started_callbacks.append(self.encoding_started)
        if self.encoding_ended not in self.encoder.encoding_ended_callbacks:
            self.encoder.encoding_ended_callbacks.append(self.encoding_ended)
        self.encoder.encode()

    def show_command(self):
        """For debug and saving command for later use."""
        self.set_encoder_settings()
        print(
            self.encoder.ffmpeg,
            " ".join([str(p) for p in self.encoder.get_parameters()]),
        )


class ErrorWidget(QWidget):
    """QWidget containing Error Message and Instructions.
    This is only used in case ffmpeg was not found via env vars."""

    def __init__(self, parent=None):
        super().__init__(parent)

        lines = QVBoxLayout()
        lines.addWidget(QLabel("Sorry but ffmpeg.exe could not be detected!"))
        lines.addWidget(QLabel("For SequenceEncoder to work you need to:"))
        lines.addWidget(QLabel("   - install ffmpeg"))
        lines.addWidget(
            QLabel(
                "   - add environment variable FFMPEG with full path to the ffmpeg executable."
            )
        )
        lines.addStretch()
        #  TODO: Enable user to pick ffmpeg and add the env var from here.
        self.setLayout(lines)
