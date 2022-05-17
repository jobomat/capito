from typing import Any, List
import pymel.core as pc

from capito.core.pipe import Pipeable, PipeableCategory


class CheckUVSets(Pipeable):
    """Check that only UV sets of specified names exist."""

    label = "UV Sets"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str]):
        """The check method."""
        uv_set_names = self.uv_sets.split(",")
        for item in items:
            try:
                shape = item.getShape()
                if not isinstance(shape, pc.nodetypes.Mesh):
                    self.messages.append(f"{shape.name()} is not of type 'Mesh'. Ignored.")
                    continue
                for uv_set in shape.getUVSetNames():
                    if uv_set not in uv_set_names:
                        self.failed = True
                        self.messages.append(f"Mesh '{shape}': UV set with name '{uv_set}' found.")
            except:
                self.messages.append(f"{item.name()} has no shape node. Ignored.")

    def get_default_parameters(self):
        return {"uv_sets": "map1"}

    def set_parameters(self, uv_sets: str = None):
        """Set parameters and maybe perform checks."""
        self.uv_sets = uv_sets

    def get_parameter_help(self, parameter):
        help = {
            "uv_sets": "A comma separated list of the expected uv set names."
        }
        return help.get(parameter, super().get_parameter_help(parameter))
