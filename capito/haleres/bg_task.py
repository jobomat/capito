import threading
import time
from subprocess import TimeoutExpired

from plumbum import local
from plumbum.commands.processes import CommandNotFound


class BGTask:
    def __init__(self, command:str, update_intervall:int=1):
        try:
            self.cmd = local[command]
        except CommandNotFound:
            self.cmd = None
            print(f"Command {command} not found.")
            return

        self.update_intervall = update_intervall
        self.parameters = []
        self.start_callbacks = []
        self.run_callbacks = []
        self.finish_callbacks = []
        self._stop = False

    def start(self):
        """Starting the threaded process and run start_callbacks"""
        if not self.cmd:
            print(f"No valid command specified.")
            return
        for callback in self.start_callbacks:
            callback()
        
        self.process = self.cmd.popen(self.parameters)

        self.start_time = time.time_ns()
        try:
            self.process.communicate(timeout=1)
        except TimeoutExpired:
            pass

        self.update_thread = threading.Thread(
            target=self.check_process, daemon=True,
        )
        self.update_thread.start()

    def check_process(self):
        """Method to call in a subprocess to check if bg job is finished.
        This Method will also state 'finished' if an error occured."""
        while self.process.poll() is None:
            if self._stop:
                break
            for callback in self.run_callbacks:
                callback()
            time.sleep(self.update_intervall)
        
        end_time = time.time_ns()
        runtime_in_seconds = (end_time - self.start_time) / 1_000_000_000

        for callback in self.finish_callbacks:
            callback(runtime_in_seconds)

    def stop(self):
        self._stop = True
        self.update_thread.join()
        self.process.terminate()
