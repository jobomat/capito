"""Module containing base classes for pipable modules."""

from dataclasses import dataclass, field
from typing import Any, List


class PipeableCategory:
    """Enables Pipeables to be categoriezed."""

    COLLECT = "Collect"
    CHECK = "Check"
    PROCESS = "Process"
    EXPORT = "Export"
    POSTPROCESS = "Postprocess"
    USER_INPUT = "User Input"
    IMPORT = "Import"

    @classmethod
    def list(cls):
        """Return the relevant order"""
        return [cls.COLLECT, cls.IMPORT, cls.CHECK, cls.PROCESS, cls.USER_INPUT, cls.EXPORT, cls.POSTPROCESS]


@dataclass
class Pipeable:
    """The base class for a pipe module."""

    # host: str
    # category: PipeableCategory
    failed: bool = False
    stop_on_failed: bool = True
    messages: list = field(default_factory=list)

    @property
    def name(self) -> str:  # pylint: disable=missing-function-docstring
        return self.__class__.__name__

    def get_default_parameters(self) -> dict:
        """Function must return a dict with the parameter names as key and the default value as value."""
        return {}

    def set_parameters(self, **kwargs):
        """Function sets parameters to the pipable instance eg:
        self.regex_pattern = regex_pattern"""
        pass

    def get_parameters(self):
        """returns all the parameters of the current pipable instance"""
        return {k: getattr(self, k) for k in self.get_default_parameters().keys()}

    def set_default_parameters(self):
        """Function sets the default parameters to the pipable instance"""
        self.set_parameters(**self.get_default_parameters())

    def get_parameter_help(self, parameter):
        """Optional function for providing help text for the pipeable module."""
        return "No help availible."

    def reset(self):
        """Reset the pipeable."""
        self.failed = False
        self.messages = []

    def execute(self, items: List[Any], exports: List[str]):
        """do whatever the pipeable should do..."""
        pass
