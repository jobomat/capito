from typing import Any, List, Dict

import pymel.core as pc
from capito.core.pipe import Pipeable, PipeableCategory


class CheckZeroGeometryArea(Pipeable):
    """Check for faces with zero area."""

    label = "No Zero Area Faces"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        """Select all items and run cleanup with 'Faces with zero geometry area' checked."""
        pc.select(items, r=True)
        pc.mel.eval(
            'polyCleanupArgList 4 { "0","2","1","0","0","0","0","0","1","1e-05","0","1e-05","0","1e-05","0","-1","0","0" };'
        )
        sel = pc.selected()
        if sel:
            self.failed = True
            self.messages.append(f"Faces with zero area deteced:\n\t\t{sel}.")
