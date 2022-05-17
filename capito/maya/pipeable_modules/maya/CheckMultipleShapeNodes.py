from typing import Any, List

from capito.core.pipe import Pipeable, PipeableCategory


class CheckMultipleShapeNodes(Pipeable):
    """Checks for multiple shape nodes in an object."""

    label = "One shape node only"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str]):
        """Check for mulitple Shape Nodes"""
        for mesh in [m for m in items if hasattr(m, "getShapes")]:
            if len(mesh.getShapes()) > 1:
                self.failed = True
                self.messages.append(f"Multiple shapes detected in {mesh.name()}.")
