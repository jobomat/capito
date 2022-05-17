from typing import Any, List
import re
from capito.core.pipe import Pipeable, PipeableCategory


class CheckNameByRegex(Pipeable):
    """Check that all objects follow a naming pattern given by a regex-pattern."""

    label = "Naming Convention"
    category = PipeableCategory.CHECK
    host = "maya"

    def set_parameters(self, regex_pattern: str = None):
        """Set the parameters needed in 'execute'."""
        self.regex_pattern = regex_pattern

    def get_default_parameters(self):
        """A regular expression to match the items names against (eg '_(geo$|grp$)')."""
        return {"regex_pattern": "_(geo$|grp$)"}

    def execute(self, items: List[Any], exports: List[str]):
        """Checks collected items follow the regex.
        This checker doesn't check if the postfix matches with object-type."""
        regex = re.compile(rf"{self.regex_pattern}")
        for item in items:
            if not regex.findall(item.name()):
                self.messages.append(
                    f"Name '{item.name()}' doesn't follow regex '{self.regex_pattern}'"
                )
                self.failed = True
