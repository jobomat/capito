import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# @dataclass
# class HostFlow:
#     """Class containing the filters, importers and publishers for a specific host.
#     filters:
#         Lists of active filters in the input section of the asset browser:
#             {"kinds": ["prop", "char",...], "steps": ["mod", "rig"...]}
#     importers:
#         Combined dict key with kind_step_extension, value is a list of relevant importers
#             host=maya, aktuelles assed kind=char: {"char_mod_ma": ["ImportReferenceMayaAscii"]}
#             host=maya, stage light: {"char_anim_abc": ["ImportAlembic"]}
#     publishers:
#         List of relevant publishers for this host-kind-step combination.
#             ["ExportModel"]
#     """
#     host: str
#     kind: str
#     filters: Dict[str, List[str]] = field(default_factory=dict)
#     importers: Dict[str, List[str]] = field(default_factory=dict)
#     publishers: Dict[str, str] = field(default_factory=dict)


@dataclass
class Flow:
    """Class representing a flow for a specific kind of asset for all hosts."""
    long_name: str
    description: str = ""
    color: str = "#333333"
    steps: Dict[str, dict] = field(default_factory=dict)



class FlowProvider:
    """The class that loads and manages all Flows."""

    def __init__(self, flow_folders: List[str] = None) -> None:
        self.flow_folders = []
        capito_project = os.environ.get("CAPITO_PROJECT_DIR")
        if capito_project:
            self.flow_folders.append(f"{capito_project}/flows/kinds")
        self.flows = {} 
        self.steps = []
        self._load_flows()

    def _load_flows(self):
        """Load all registered Flows"""
        for folder in self.flow_folders:
            for flowfile in Path(folder).glob("*.json"):
                self.load_flow(flowfile)
        self.kinds = self._get_kinds()

    def load_flow(self, flowfile:str):
        """Load a single flowfile.
        Existing Flows of the same name will be replaced."""
        flowpath = Path(flowfile)
        flow = Flow(**json.loads(flowpath.read_text()))
        self.flows[flowpath.stem] = flow
        self.steps.extend(list(flow.steps.keys()))
        self.steps = sorted(list(set(self.steps)))

    def _get_kinds(self) -> List[str]:
        """Return a list of all defined kinds.
        eg: ["char", "prop", ...]
        """
        return sorted(list(self.flows.keys()))

    def reload(self):
        self.flows = {}
        self.steps = []
        self._load_flows()


#  FLOWS = FlowProvider()