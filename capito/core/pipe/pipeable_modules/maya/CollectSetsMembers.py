from typing import Any, List, Dict
import re

import pymel.core as pc
from capito.core.pipe import Pipeable, PipeableCategory


class CollectSetsMembers(Pipeable):
    """Collect members of sets.
Only sets with names matching the set_regex will be searched.
If a set was found only set members with names matching the member_regex will be included."""

    label = "Members of Sets"
    category = PipeableCategory.COLLECT
    host = "maya"

    def set_parameters(self, set_regex: str=None, collect_set: bool=None, member_regex: str=None):
        """Set the parameters needed in 'execute'."""
        self.set_regex = set_regex
        self.member_regex = member_regex

    def get_default_parameters(self):
        """Provide default parameters needed in 'execute'."""
        return {
            "set_regex": ".*_geoset",
            "member_regex": ".*_geo"
        }

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        """Search for sets matching the pattern and collect the Members."""
        maya_sets = pc.ls(sets=True, regex=self.set_regex)
        if not maya_sets:
            self.messages.append(f"No sets matching the regex '{self.set_regex}' where found.")
            self.failed = True
            return
        members = []
        self.messages.append(f"Detected {len(maya_sets)} set(s) matching regex '{self.set_regex}'.")
        for maya_set in maya_sets:
            members.extend(maya_set.members())
            if not members:
                self.messages.append(f"No members in set '{maya_set}'.")
        if not members:
            self.messages.append(f"No set members detected.")
            self.failed = True
            return
        
        regex = re.compile(rf"{self.member_regex}")
        members = [m for m in members if regex.findall(m.name())]
        if members:
            self.messages.append(f"Collected {len(members)} Objects.")
            items.extend(members)
        else:
            self.messages.append(f"No members matching the regex '{self.member_regex}' where found.")
            self.failed = True
