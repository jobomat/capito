from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class HostFlow:
    """Class containing the filters, importers and publishers for a specific host.
    filters:
        Lists of active filters in the input section of the asset browser: 
            {"kinds": ["prop", "char",...], "steps": ["mod", "rig"...]}
    importers:
        Combined dict key with kind_step_extension, value is a list of relevant importers
            host=maya, aktuelles assed kind=char: {"char_mod_ma": ["ImportReferenceMayaAscii"]}
            host=maya, stage light: {"char_anim_abc": ["ImportAlembic"]}
    publishers:
        List of relevant publishers for this host-kind-step combination.
            ["ExportModel"]
    """
    host: str
    kind: str
    filters: Dict[str, List[str]] = field(default_factory=dict)
    importers: Dict[str, List[str]] = field(default_factory=dict)
    publishers: Dict[str, str] = field(default_factory=dict)


@dataclass
class Flows:
    """Class representing all flows for a specific kind of asset for all hosts."""
    name: str
    description: str = ""
    steps: Dict[str, HostFlow] = field(default_factory=dict)
    color: str = "#333333"
