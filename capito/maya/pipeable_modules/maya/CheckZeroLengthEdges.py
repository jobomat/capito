from typing import Any, List

import pymel.core as pc
from capito.core.pipe import Pipeable, PipeableCategory


class CheckZeroLengthEdges(Pipeable):
    """Check for edges with zero length."""

    label = "No Zero Length Edges"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str]):
        """Select all items and run cleanup with 'Edges with zero length' checked."""
        pc.select(items, r=True)
        pc.mel.eval(
            'polyCleanupArgList 4 { "0","2","1","0","0","0","0","0","0","1e-05","1","1e-05","0","1e-05","0","-1","0","0" };'
        )
        sel = pc.selected()
        if sel:
            self.failed = True
            self.messages.append(f"Edges with zero length deteced:\n\t\t{sel}.")
