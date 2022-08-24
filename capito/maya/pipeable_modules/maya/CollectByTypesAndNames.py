import re
from typing import Any, List

import pymel.core as pc
from capito.core.pipe import Pipeable, PipeableCategory


class CollectByTypesAndNames(Pipeable):
    """Collect objects
    - of certain PyMel types (transform,camera,mesh...)
    - matching a certain name (regex)"""

    label = "By Type and Name"
    category = PipeableCategory.COLLECT
    host = "maya"

    def set_parameters(
        self,
        regex_pattern: str = None,
        types: str = None,
        exclude_default_nodes: bool = True,
        exclude_shared_nodes: bool = True,
    ):
        """Set the parameters needed in 'execute'."""
        self.regex_pattern = regex_pattern
        self.types = types
        self.exclude_default_nodes = exclude_default_nodes
        self.exclude_shared_nodes = exclude_shared_nodes

    def get_default_parameters(self):
        """Provide default parameters needed in 'execute'."""
        return {
            "regex_pattern": ".*",
            "types": "transform",
            "exclude_default_nodes": True,
            "exclude_shared_nodes": True,
        }

    def execute(self, items: List[Any], exports: List[str]):
        """Search for sets matching the pattern and collect the Members."""
        regex = re.compile(rf"{self.regex_pattern}")
        type_list = [t.strip() for t in self.types.split(",")]
        type_message = ""

        matches = [m for m in pc.ls() if regex.findall(m.name(stripNamespace=False))]

        if self.types:
            matches = [m for m in matches if m.type() in type_list]
            type_message = f" of type(s) '{self.types}'"

        if self.exclude_default_nodes:
            matches = [m for m in matches if not m.isDefaultNode()]

        if self.exclude_shared_nodes:
            matches = [m for m in matches if not m.isShared()]

        if not matches:
            self.messages.append(
                f"No objects matching the regex '{self.regex_pattern}'{type_message} where found."
            )
            self.failed = True
            return

        self.messages.append(f"Collected {len(matches)} object(s){type_message}.")
        items.extend(matches)

    def get_parameter_help(self, parameter):
        help = {
            "regex_pattern": "The regex pattern to filter the name against.",
            "types": "A comma separated list of pymel types. Leave blank for all types!",
            "exclude_default_nodes": "Do not collect default nodes (eg. initialShadingGroup).",
            "exclude_shared_nodes": "Do not collect shared nodes (eg. persp, top...).",
        }
        return help.get(parameter, super().get_parameter_help(parameter))


pc.ls
