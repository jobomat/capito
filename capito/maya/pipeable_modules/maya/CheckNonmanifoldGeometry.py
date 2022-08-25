from typing import Any, List, Dict

import pymel.core as pc
from capito.core.pipe import Pipeable, PipeableCategory


class CheckNonmanifoldGeometry(Pipeable):
    """Check for nonmanifold geometry (Normals and Geo)."""

    label = "No Nonmanifold Geometry"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        """Select all items and run cleanup with only nonmanifold checked."""
        pc.select(items, r=True)
        pc.mel.eval(
            'polyCleanupArgList 4 { "0","2","1","0","0","0","0","0","0","1e-05","0","1e-05","0","1e-05","0","1","0","0" };'
        )
        sel = pc.selected()
        if sel:
            self.failed = True
            self.messages.append(f"Nonmanifold geometry deteced.\n\t\t{sel}.")
