from pathlib import Path
import json
from PySide6.QtWidgets import QFileDialog

import pymel.core as pc


class HUDs:
    def __init__(self):
        self.current_huds = {}
        self.remember_current()
        
    def list(self):
        return pc.headsUpDisplay(lh=True)

    def remember_current(self):
        self.current_huds = self.get()
        
    def get(self) -> dict:
        result = {}
        for hud in self.list():
            result[hud] = pc.headsUpDisplay(hud, q=True, vis=True)
        return result
         
    def recall_current(self):
        self.set(self.current_huds)
            
    def hide_all(self):
        for hud in self.list():
            pc.headsUpDisplay(hud, e=True, vis=False)
        pc.mel.eval("toggleAxis -o 0;")
        pc.mel.eval("viewManip -v 0;")
            
    def set(self, huds:dict):
        for hud, option in huds.items():
            pc.headsUpDisplay(hud, e=True, vis=option)
            
    def save(self):
        files = pc.fileDialog2(fileFilter="*.json", dialogStyle=2, fileMode=1)
        if files:
            file = Path(files[0])
            with file.open("w") as jf:
                json.dump(self.get(), jf)
                
    def load(self):
        filename = QFileDialog.getOpenFileName(
            None, "Load HUD Config", filter="JSON (*.json)"
        )
        if not filename[0]:
            return
        hud_file = Path(filename[0])
        with hud_file.open("r") as filehandle:
            self.set(json.load(filehandle))