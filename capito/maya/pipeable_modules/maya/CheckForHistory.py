from typing import Any, List

from capito.core.pipe import Pipeable, PipeableCategory


class CheckForHistory(Pipeable):
    """Check shape nodes of items for history (input-nodes).
Fails if history is detected."""

    label = "History"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str]):
        """The check method."""
        for mesh in [m for m in items if m.type() in self.types.split(",")]:
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
