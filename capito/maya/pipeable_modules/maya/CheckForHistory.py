from typing import Any, List, Dict

import pymel.core as pc

from capito.core.pipe import Pipeable, PipeableCategory


class CheckForHistory(Pipeable):
    """Check shape nodes of items for history (input-nodes).
Fails if history is detected."""

    label = "History"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        """The check method."""
        type_list = [t.strip() for t in self.types.split(",")]
        for mesh in [m for m in items if m.type() in type_list]:
            shape = mesh
            if isinstance(mesh, pc.nodetypes.Transform):
                shape = mesh.getShape()
            if shape is None:
                continue
            connections = shape.connections(s=True, d=False)
            if connections:
                self.failed = True
                self.messages.append(f"Object '{mesh}' has history.")

    def get_default_parameters(self):
        """A comma separated list of pymel types (transform, mesh, camera...)"""
        return {"types": "transform"}

    def set_parameters(self, types: str = None):
        """Set parameters and maybe perform checks."""
        self.types = types

    def get_parameter_help(self, parameter):
        help = {
            "types": "A comma separated list of pymel types (transform, mesh, camera...)"
        }
        return help.get(parameter, super().get_parameter_help(parameter))
