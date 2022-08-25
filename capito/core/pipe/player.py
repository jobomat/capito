"""Module providing PipelinePlayer class."""
import json
from pathlib import Path
from typing import Callable, List

from capito.core.pipe.models import Pipeable
from capito.core.pipe.provider import PipeProvider

# def to_type(line):
#     key_type, value = [x.strip() for x in line.split("=")]
#     key, type = [x.strip() for x in key_type.split(":")]
#     caster = {
#         "int": int,
#         "float": float,
#         "bool": bool,
#         "str": str,
#         "env": lambda x: os.environ[x],
#     }
#     if type == "str":
#         value = value[1:-1]
#     elif type == "bool":
#         value = True if value == "True" else False
#     return key, caster[type](value)


# code = """FILENAME: str = "test"
# STARTFRAME: int = 1
# ENDFRAME: int = 20
# TEST: float = 1.5
# TEST2: bool = False
# TEST3: env = MAYA_APP_DIR
# """

# globals = {}

# for line in code.split("\n"):
#     if not line:
#         continue
#     key, value = to_type(line)
#     globals[key] = value


def print_reporter(reportable: Pipeable):
    """Report by printing to console."""
    print(reportable.category, reportable.label)
    print("\t", "Failed" if reportable.failed else "Passed")
    for message in reportable.messages:
        print("\t", message)


class PipePlayer:
    """Manages a playlist of Pipeables.
    The playlist can be run.
    The results can be passed to callback functions.
    """

    def __init__(
        self, provider: PipeProvider, reporter_callbacks: List[Callable] = None
    ):
        self.provider = provider
        self.items = []
        self.exports = []
        self.playlist: List[Pipeable] = []
        self.stopped = False
        self.title = "New Playlist"
        self.description = "No description available."
        self.user_input = {}

        self.reporter_callbacks = [print_reporter]
        if reporter_callbacks is not None:
            self.reporter_callbacks.extend(reporter_callbacks)

    def append_new(
        self, module_name: str, stop_on_failed: bool = None, parameters: dict = None
    ):
        """Creates an instance of 'mudule_name' and appends it to the player"""
        if module_name not in self.provider.modules:
            raise KeyError(f"Module {module_name} not availible in PipeProvider.")
        class_instance = self.provider.get_instance(module_name)
        class_instance.stop_on_failed = stop_on_failed
        if parameters:
            class_instance.set_parameters(**parameters)
        self.playlist.append(class_instance)

    def append_existing(self, class_instance: Pipeable):
        """Append an already loaded Pipeable class."""
        self.playlist.append(class_instance)

    def call_reporters(self, reportable: Pipeable):
        """Calls all registered reporters."""
        for reporter in self.reporter_callbacks:
            reporter(reportable)

    def play(self):
        """The collect, check, export, process... function."""
        self.stopped = False
        self.items = []
        for class_instance in self.playlist:
            if self.stopped:
                break
            class_instance.reset()
            class_instance.execute(self.items, self.exports, self.user_input)
            self.call_reporters(class_instance)
            if class_instance.failed and class_instance.stop_on_failed:
                self.stopped = True

    def reset(self):
        """Reset the playlist."""
        self.playlist.clear()
        self.items.clear()
        self.exports.clear()

    def as_list(self):
        """Return the playlist as python list (eg. for json export)."""
        return [
            {
                "name": m.name,
                "parameters": m.get_parameters(),
                "stop_on_failed": bool(m.stop_on_failed),
            }
            for m in self.playlist
        ]

    def append_from_list(self, mod_list):
        """Append all the modules listed in mod_list."""
        for mod in mod_list:
            self.append_new(mod["name"], mod["stop_on_failed"], mod["parameters"])

    def load(self, playlist_file: Path):
        """Load a playlist-json."""
        self.reset()
        with playlist_file.open("r") as json_file:
            loaded_list = json.load(json_file)
        self.append_from_list(loaded_list["playlist"])
        self.title = playlist_file.stem
        self.description = loaded_list["description"]

    def save(self, playlist_file: Path):
        """Save a playlist-json."""
        to_save = {"description": self.description, "playlist": self.as_list()}
        with playlist_file.open("w") as json_file:
            json.dump(to_save, json_file, indent=4)
