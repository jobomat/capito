from typing import Any, List, Dict

from capito.core.pipe import Pipeable, PipeableCategory


class CheckFreezedRotateValues(Pipeable):
    """Check for freezed rotate channels.
Fails if rotate channels differ from (0, 0, 0)."""

    label = "Rotate = (0,0,0)"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        """Check for Freeze Transforms: Rotate"""
        for transform in [t for t in items if t.type() == "transform"]:
            rotations_are_zero = [x == 0.0 for x in transform.getRotation()]
            if not all(rotations_are_zero):
                self.messages.append(
                    f"Object '{transform}' has nonzero rotation values."
                )
                self.failed = True
