import os
import re
import threading
import time
from pathlib import Path
from subprocess import TimeoutExpired
from tracemalloc import start

from capito.core.decorators import layered_settings
from capito.core.encoder.util import DrawText
from capito.core.helpers import get_font_file, remap_value

from plumbum import local
from plumbum.commands.processes import CommandNotFound

ffmpeg_path = os.environ.get("FFMPEG", "ffmpeg")  # path or "ffmpeg"
try:
    ffmpeg = local[ffmpeg_path]
except CommandNotFound:
    ffmpeg = None


@layered_settings(["default","project","projectuser","user"])
class SequenceEncoder:
    def __init__(self,input_pattern:str=None, output_file:str=None,
                 startframe:int=0, endframe:int=0, preset: str = None):
        self.ffmpeg = ffmpeg
        self._layered_settings = self._get_layered_settings()

        self.load_preset(preset)

        self.startframe = startframe
        self.endframe = endframe
        self.encoding_started_callbacks = []
        self.encoding_ended_callbacks = []
        self.output_file = output_file
        self.input_pattern = input_pattern

    def load_preset(self, preset:str=None):
        if preset:
            preset = f"PRESET:{preset}"
        else:
            preset = f"PRESET:{self.get_availible_presets()[0]}"
        self.framerate = self._layered_settings[preset]["framerate"]
        self.quality = self._layered_settings[preset]["quality"]
        self.burnin_defaults = self._layered_settings[preset]["burnin_defaults"]
        self.burnins = self._layered_settings[preset]["burnins"]

    def get_availible_presets(self):
        return [
            p[7:] for p in self._layered_settings.dict if p.startswith("PRESET:")
        ]

    def get_current_settings(self):
        return {
            "framerate": self.framerate,
            "quality": self.quality,
            "burnin_defaults": self.burnin_defaults,
            "burnins": self.burnins
        }

    def is_ready(self):
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
        return self.endframe - self.startframe

    def get_end_time(self):
        return self.get_number_of_frames() / self.framerate

    def get_quality(self):
        """Map 0-100 quality to ffmpeg specific values"""
        return remap_value(0, 100, 32, 15, self.quality)

    def get_drawtext(self):
        dt = []
        for pos, text in self.burnins.items():
            drawtext = DrawText(pos, text, self)
            dt_string = drawtext.get_drawtext()
            if dt_string:
                dt.append(f"drawtext={dt_string}")
        if dt:
            return f"[IN]{','.join(dt)}[OUT]"

    def check_process(self):
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

    def encode(self):
        if not self.output_file:
            print("Please specify an output file.")
            return
        if not self.input_pattern:
            print("Please specify an input sequence.")
            return

        burnins = self.get_drawtext()
            
        parameters = [
            "-framerate", self.framerate,
            "-start_number", self.startframe,
            "-i", self.input_pattern,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-y",  # Overwrite if existing
            "-crf", self.get_quality(),
            "-t", self.get_end_time()
        ]
        if burnins:
            parameters.append("-vf")
            parameters.append(burnins)
        parameters.append(self.output_file)
        
        # print(parameters)
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
