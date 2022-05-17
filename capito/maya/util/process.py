from dataclasses import dataclass
import threading
import subprocess
import tempfile
import time
import os
import sys
from pathlib import Path

import pymel.core as pc

from capito.maya.util.ports import open_port


class SubQ:
    """
    A class to run commandline processes from Maya.
    The added commands will not run in parallel but one after another.
    This enables the commands to use generated files from their predecessors.
    For Example:
    Render an image sequence via Mayabatch and then convert it to mp4 via ffmpeg.

    The command strings have to be properly escaped and executable by the OS.
    'echo test1 >> "E:\\folder with spaces\\test1.txt"'
    There will be no checks concerning the added commands but errors will be logged.

    Usage:
    sq = SubQ()
    sq.add('Render -s 1 -e 10 -pad 4 -r hw2 -rd E:\\images -im test')
    sq.add('ffmpeg -r 25 -crf 25 -i test.%04d.png test.mp4')
    sq.run()
    """

    def __init__(self, error_log=None):
        self.q = []
        self.error_log = (
            error_log
            if error_log is not None
            else tempfile.mkstemp(prefix="SubQ_ERROR_", suffix=".log")[-1]
        )
        self.port = 2345
        open_port(self.port)
        self.mayapy = Path(sys.executable).parent / "mayapy"

    def add(self, cmd):
        """Add a command string to the queue."""
        self.q.append(cmd)

    def run(self):
        with open(self.error_log, "w") as log:
            log.write(f"Started: {time.ctime()}\n")
        print(f"Sub Process started. Queue length: {len(self.q)}")
        print(f"Errors will be logged to '{self.error_log}'")
        t = threading.Thread(target=self.get_process_function())
        t.daemon = True
        t.start()

    def get_cmds(self):
        return " && ".join(self.q)

    def get_process_function(self):
        def process():
            with open(self.error_log, "a") as log:
                subprocess.check_call(self.get_cmds(), shell=True, stderr=log)

        return process

    def reset(self):
        self.q = []

    def add_message(self, message):
        cmd = f"\"{self.mayapy}\" -c \"import socket;s=socket.socket(socket.AF_INET, socket.SOCK_STREAM);s.connect(('localhost', {self.port}));s.send(b'import pymel.core as pc;pc.warning(\\'{message}\\')');s.close()\""
        self.add(cmd)

    def length(self):
        return len(self.q)


"""
from capito.maya.util.process import SubQ
from capito.maya.render.processes import Ffmpeg, BatchRender

sq = SubQ()

br = BatchRender(e=100)

ff = Ffmpeg(exe="C:/Program Files/ffmpeg/bin/ffmpeg.exe")

ff.input = "F:/mayaProjects/studi_help/images/rotating_cube.%04d.png"
ff.output = f"F:/rotating_cube_hw.mp4"
ff.quality = 15
ff.text["left"].append("Crazy Show")
ff.text["left"].append(pc.system.sceneName())
ff.text["left"].append("datetime")
ff.text["right"].append("Cam: Shotcam2")
ff.text["right"].append("frame")

sq.add(br.cmd())
sq.add_message("Rendering finished.")
sq.add(ff.cmd())
sq.add_message("Encoding finished.")

sq.run()
"""
