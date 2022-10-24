from typing import Any, List, Dict

from capito.core.pipe import Pipeable, PipeableCategory


class CheckFreezedScaleValues(Pipeable):
    """Check for freezed scale channels.
Fails if scale is not (1, 1, 1)."""

    label = "Scale = (1,1,1)"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        """Check for Freeze Transforms: Scale"""
        for transform in [t for t in items if t.type() == "transform"]:
            scales_are_one = [x == 1.0 for x in transform.getScale()]
            if not all(scales_are_one):
                self.messages.append(
                    f"Object '{transform}' has scale values different from (1,1,1)."
                )
                self.failed = True
