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

    @classmethod
    def list(cls):
        """Return the relevant order"""
        return [cls.COLLECT, cls.CHECK, cls.PROCESS, cls.EXPORT, cls.POSTPROCESS]


@dataclass
class Pipeable:
    """The base class for a pipe module."""

    # host: str
    # category: PipeableCategory
    failed: bool = False
    stop_on_failed: bool = True
    messages: list = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def get_default_parameters(self) -> dict:
        return {}

    def set_parameters(self, **kwargs):
        pass

    def get_parameters(self):
        return {k: getattr(self, k) for k in self.get_default_parameters().keys()}

    def set_default_parameters(self):
        self.set_parameters(**self.get_default_parameters())

    def get_parameter_help(self, parameter):
        return "No help availible."

    def reset(self):
        self.failed = False
        self.messages = []

    def execute(self, items: List[Any], exports: List[str]):
        pass
