from pathlib import Path
from typing import Any, List, Dict

from capito.core.pipe import Pipeable, PipeableCategory


class ResetCollectedItems(Pipeable):
    """Reset the collected items list."""

    label = "Reset Items List"
    category = PipeableCategory.COLLECT
    host = "system"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        items.clear()
        self.messages.append(
            f"Collected items list resetted."
        )