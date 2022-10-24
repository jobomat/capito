from typing import Any, List, Dict
from collections import Counter

from capito.core.pipe import Pipeable, PipeableCategory


class CheckUniqueNames(Pipeable):
    """Check that all collected objects have a unique name."""

    label = "Unique Names"
    category = PipeableCategory.CHECK
    host = "maya"

    # def set_parameters(self, regex_pattern: str = None):
    #     """Set the parameters needed in 'execute'."""
    #     self.regex_pattern = regex_pattern

    # def get_default_parameters(self):
    #     """A regular expression to match the items names against (eg '_(geo$|grp$)')."""
    #     return {"regex_pattern": "_(geo$|grp$)"}

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        """Check the items on uniqueness of names."""
        count = Counter([o.name(long=None) for o in items])
        for name, num in count.items():
            if num != 1:
                self.messages.append(f"{num} objects are named '{name}'.")
                self.failed = True
