from pathlib import Path
from typing import Any, List, Dict

from capito.core.pipe import Pipeable, PipeableCategory


class CollectFilesInFolder(Pipeable):
    """Collect all files in a specific folder."""

    label = "Collect Files in Folder"
    category = PipeableCategory.COLLECT
    host = "system"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        path = Path(self.folder)
        matches = [m for m in path.glob(self.name_pattern) if m.is_file()]
        if matches:
            for match in matches:
                self.messages.append(f"Collected file '{match}'.")
            items.extend(matches)
            return
        self.failed = True
        self.messages.append(
            f"No matching files for pattern '{self.name_pattern}' in folder '{self.folder}'."
        )

    def set_parameters(self, folder: str, name_pattern: str):
        self.folder = folder
        self.name_pattern = name_pattern

    def get_default_parameters(self):
        """Default parameters."""
        return {"folder": str(Path().home()).replace("\\","/"), "name_pattern": "*"}

    def get_parameter_help(self, parameter):
        help = {
            "folder": "The absolute path of the folder to scan.",
            "name_pattern": "A regex pattern of files to list (eg. '*.py')"
        }

        return help.get(parameter, super().get_parameter_help(parameter))
