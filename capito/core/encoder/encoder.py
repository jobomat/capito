"""Module for a image sequence to mp4 encoder"""
import os
import threading
import time
from subprocess import TimeoutExpired

from capito.core.decorators import layered_settings
from capito.core.encoder.util import DrawText
from capito.core.helpers import remap_value
from plumbum import local
from plumbum.commands.processes import CommandNotFound

FFMPEG_PATH = os.environ.get("FFMPEG", "ffmpeg")
try:
    FFMPEG = local[FFMPEG_PATH]
except CommandNotFound:
    FFMPEG = None


@layered_settings(["default", "project", "projectuser", "user"])
class SequenceEncoder:
    """Class for encoding image sequences to mp4 via ffmpeg."""

    def __init__(
        self,
        input_pattern: str = None,
        output_file: str = None,
        startframe: int = 0,
        endframe: int = 0,
        preset: str = None,
        show_command: bool = False,
    ):
        self.ffmpeg = FFMPEG
        self._layered_settings = self._get_layered_settings()

        self.load_preset(preset)

        self.startframe = startframe
        self.endframe = endframe
        self.encoding_started_callbacks = []
        self.encoding_ended_callbacks = []
        self.output_file = output_file
        self.input_pattern = input_pattern
        self.show_command = show_command

    def load_preset(self, preset: str = None):
        """Load a preset for quality, framerate and burnin settings."""
        if preset:
            preset = f"PRESET:{preset}"
        else:
            preset = f"PRESET:{self.get_availible_presets()[0]}"
        self.framerate = self._layered_settings[preset]["framerate"]
        self.quality = self._layered_settings[preset]["quality"]
        self.burnin_defaults = self._layered_settings[preset]["burnin_defaults"]
        self.burnins = self._layered_settings[preset]["burnins"]

    def get_availible_presets(self):
        """Get the presets from the layered_settings file."""
        return [p[7:] for p in self._layered_settings.dict if p.startswith("PRESET:")]

    def get_current_settings(self):
        """Return the current settings as a dict (e.g. for usage in presets)."""
        return {
            "framerate": self.framerate,
            "quality": self.quality,
            "burnin_defaults": self.burnin_defaults,
            "burnins": self.burnins,
        }

    def is_ready(self):
        """Method to check if the encoder can be used."""
        is_ready = self.ffmpeg is not None
        if not is_ready:
            print("Sorry but ffmpeg.exe could not be detected!")
            print("For SequenceEncoder to work you need to:")
            print("   - install ffmpeg")
            print(
                "   - add environment variable FFMPEG with full path to the ffmpeg executable."
            )
        return is_ready

    def get_number_of_frames(self):
        """Convenience method for calculating sequence length."""
        return self.endframe - self.startframe

    def get_end_time(self):
        """Get the time-lengts of the clip as a function of frames and framerate"""
        return self.get_number_of_frames() / self.framerate

    def get_quality(self):
        """Map 0-100 quality to ffmpeg specific values"""
        return remap_value(0, 100, 32, 15, self.quality)

    def get_drawtext(self):
        """Return the complete ffmpeg drawtext string."""
        dt = []
        for pos, text in self.burnins.items():
            drawtext = DrawText(pos, text, self)
            dt_string = drawtext.get_drawtext()
            if dt_string:
                dt.append(f"drawtext={dt_string}")
        if dt:
            return f"[IN]{','.join(dt)}[OUT]"

    def check_process(self):
        """Method to call in a subprocess to check if encoding is finished.
        This Method will also state 'finished' if an error occured."""
        while self.process.poll() is None:
            print("  Encoding in progress...")
            time.sleep(1)
        encoding_end_time = time.time_ns()
        encoded_in_seconds = (
            encoding_end_time - self.encoding_start_time
        ) / 1_000_000_000
        for callback in self.encoding_ended_callbacks:
            callback(encoded_in_seconds)
        print(f"Encoding finished in {encoded_in_seconds} seconds.")

    def get_parameters(self):
        """Assemble all the parameters into a list for plumbum.popen"""
        burnins = self.get_drawtext()

        parameters = [
            "-framerate",
            self.framerate,
            "-start_number",
            self.startframe,
            "-i",
            self.input_pattern,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-y",  # Overwrite if existing
            "-crf",
            self.get_quality(),
            "-t",
            self.get_end_time(),
        ]
        if burnins:
            parameters.append("-vf")
            parameters.append(burnins)
        parameters.append(self.output_file)
        return parameters

    def encode(self):
        """Method that uses the provided data to generate a ffmpeg call."""
        if not self.output_file:
            print("Please specify an output file.")
            return
        if not self.input_pattern:
            print("Please specify an input sequence.")
            return

        parameters = self.get_parameters()

        for callback in self.encoding_started_callbacks:
            callback()
        print("Encoding started...")

        self.process = self.ffmpeg.popen(parameters)
        self.encoding_start_time = time.time_ns()
        try:
            self.process.communicate(timeout=1)
        except TimeoutExpired:
            pass

        self.update_thread = threading.Thread(target=self.check_process, daemon=True)
        self.update_thread.start()
