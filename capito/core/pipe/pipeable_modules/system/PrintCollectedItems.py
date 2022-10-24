from pathlib import Path
from typing import Any, List, Dict

from capito.core.pipe import Pipeable, PipeableCategory


class PrintCollectedItems(Pipeable):
    """Print all the collected items to this point."""

    label = "Print Items List"
    category = PipeableCategory.DEBUG
    host = "system"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        self.messages.append(
            f"Collected items:"
        )
        for item in items:
            self.messages.append(str(item))

    def set_default_parameters(self):
        self.stop_on_failed = False