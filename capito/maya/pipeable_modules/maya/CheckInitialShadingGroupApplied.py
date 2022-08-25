from typing import Any, List, Dict

from capito.core.pipe import Pipeable, PipeableCategory


class CheckInitialShadingGroupApplied(Pipeable):
    """Check that only 'initialShadingGroup' is applied."""

    label = "Initial Shading Group"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        """Check for shadingEngines with name other than 'initialShadingGroup'."""
        for mesh in [m for m in items if hasattr(m, "getShapes")]:
            connections = mesh.getShape().connections(type="shadingEngine")
            if connections[0].name() != "initialShadingGroup":
                self.messages.append(f"Object '{mesh}' has shaders assigned.")
                self.failed = True
