from pathlib import Path
from typing import Any, Dict, List

from capito.core.pipe import Pipeable, PipeableCategory
from PySide2.QtWidgets import QDialog  # pylint:disable=wrong-import-order
from PySide2.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class InputFiles(Pipeable):
    """Asks user to specify one file that may or may not exist or multiple files (that must exist)."""

    label = "Choose file(s)"
    category = PipeableCategory.INPUT
    host = "system"

    def set_parameters(
        self,
        dialog_title: str,
        multiple_files: bool,
        existing_files: bool,
        start_dir: str,
        filetype_filter: str,
    ):
        """set"""
        self.dialog_title = dialog_title
        self.multiple_files = multiple_files
        self.existing_files = existing_files
        self.start_dir = start_dir
        self.filetype_filter = filetype_filter

    def get_default_parameters(self):
        """Default parameters."""
        return {
            "dialog_title": "Please select a File",
            "multiple_files": False,
            "existing_files": True,
            "start_dir": ".",
            "filetype_filter": "Text files (*.txt)",
        }

    def get_parameter_help(self, parameter):
        "get help"
        help = {
            "dialog_title": "The title of the file chooser dialog window.",
            "multiple_files": "Check if user should be able to select multiple files.",
            "existing_files": "Only existing files can be selectd. Always TRUE if 'multiple_files' is checked.",
            "start_dir": "The file chooser will start in this directory.",
            "filetype_filter": "A filter mask. Leave blank if all files should be visible.",
        }

        return help.get(parameter, super().get_parameter_help(parameter))

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        "The actual function to execute."
        if self.multiple_files:
            dialog_type = "getOpenFileNames"  # file has to exist, one file
        else:
            dialog_type = (
                "getOpenFileName" if self.existing_files else "getSaveFileName"
            )
        result = getattr(QFileDialog, dialog_type)(
            None, self.dialog_title, self.start_dir, self.filetype_filter
        )
        if result[0]:
            if isinstance(result[0], list):
                items.extend(result[0])
            else:
                items.append(result[0])
            self.messages.append(f"'{result[0]}' was chosen by user.")
        else:
            self.failed = True
            self.messages.append("User did not choose any file.")
