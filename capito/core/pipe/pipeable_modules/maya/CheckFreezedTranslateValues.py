from typing import Any, List, Dict

from capito.core.pipe import Pipeable, PipeableCategory


class CheckFreezedTranslateValues(Pipeable):
    """Check for freezed translate channels.
Fails if translate channels are not (0, 0, 0)."""

    label = "Translate = (0,0,0)"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        """Check for Freezed Translate Values"""
        for transform in [t for t in items if t.type() == "transform"]:
            translates_are_zero = [x == 0.0 for x in transform.getTranslation()]
            if not all(translates_are_zero):
                self.messages.append(
                    f"Object '{transform}' has nonzero transformation values."
                )
                self.failed = True
