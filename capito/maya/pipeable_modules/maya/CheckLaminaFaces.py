from typing import Any, List

import pymel.core as pc
from capito.core.pipe import Pipeable, PipeableCategory


class CheckLaminaFaces(Pipeable):
    """Check that no lamina faces exist."""

    label = "Lamina Faces"
    category = PipeableCategory.CHECK
    host = "maya"

    def execute(self, items: List[Any], exports: List[str]):
        """Select all items and run cleanup with only lamina faces checked."""
        pc.select(items, r=True)
        pc.mel.eval(
            'polyCleanupArgList 4 { "0","2","1","0","0","0","0","0","0","1e-05","0","1e-05","0","1e-05","0","-1","1","0" };'
        )
        sel = pc.selected()
        if sel:
            self.failed = True
            self.messages.append(f"Lamina Faces deteced.\n\t\t{sel}.")
