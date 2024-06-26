"""Module for communicating with hlrs (e.g. hawk).
This module needs the haleres venv interpreter (fabric)
"""
import os
from pathlib import Path
from subprocess import Popen, check_output, CalledProcessError
import time
from datetime import datetime
from typing import List

import fabric

from capito.haleres.settings import Settings
from capito.haleres.job import Job


def vpn_running() -> bool:
    try:
        vpn_status = check_output(["systemctl","status","vpn"], universal_newlines=True)
        return vpn_status.endswith("Tunnel is up and running.\n")
    except CalledProcessError:
        return False


def vpn_start() -> bool:
    result = check_output(["systemctl","start","vpn"], universal_newlines=True)
    time.sleep(1)
    return vpn_running()


def vpn_stop(self):
    result = check_output(["systemctl","stop","vpn"], universal_newlines=True)
    return not vpn_running()


def parse_ws_list_result(ws_list_result: list) -> List[dict]:
    workspaces = []
    ws_info = {}
    for line in ws_list_result:
        key, *val = line.split(":")
        if not key:
            continue
        if key == "id":
            if ws_info:
                workspaces.append(ws_info)
        ws_info[key.strip()] = ":".join(val).strip()
        
    if ws_info:
        workspaces.append(ws_info)

    return workspaces


class HLRSWorkspace:
    def __init__(self, ws_dict: dict):
        self.ws_dict = ws_dict 
        self.name: str = ws_dict.get("id")
        self.path: str = ws_dict.get("workspace directory")
        self.remaining_time: str = ws_dict.get("remaining time")
        self.creation_date: str = ws_dict.get("creation time")
        self.expiration_date: str = ws_dict.get("expiration date")
        self.filesystem_name: str = ws_dict.get("filesystem name")
        self.available_extensions: int = int(ws_dict.get("available extensions", 0))


class HLRS:
    def __init__(self, settings_file:str):
        self.settings = Settings(settings_file)

        if not vpn_running():
            vpn_start()

        self.connection = self.connect()

        self.workspaces = self.load_workspaces()
        self.workspace:HLRSWorkspace = None
        self.set_current_workspace()

    def connect(self) -> fabric.Connection:
        return fabric.Connection(host=self.settings.hlrs_server, user=self.settings.hlrs_user)
    
    def connection_established(self) -> bool:
        pass
    
    def run(self, cmd: str) -> List[str]:
        result = self.connection.run(cmd, hide=True)
        return [line.rstrip() for line in result.stdout.strip().split("\n")]
    
    def load_workspaces(self) -> List[dict]:
        return parse_ws_list_result(self.run(self.settings.ws_list))
    
    def set_current_workspace(self, workspace_name:str=None):
        if not self.workspaces:
            # There are no workspaces found on HLRS
            return False
        if workspace_name is None:
            workspace_name = self.workspaces[0]["id"]
        ws = next((w for w in self.workspaces if w['id'] == workspace_name), None)
        if ws is not None:
            self.workspace = HLRSWorkspace(ws)
            # print(f"Workspace {self.workspace.name} set.")
            return True
        # print(f"Workspace {workspace_name} doesn't seem to exist.")       

    def list_renderers(self) -> List[str]:
        return self.folder_listing("renderers")

    def qstat(self) -> list:
        return self.run(self.settings.qstat)
    
    def get_current_running_jobs(self) -> list:
        return [job for job in self.qstat() if job]
    
    def folder_listing(self, directory: str):
        d = f"{self.workspace.path}/{directory}"
        files = f'find {d} -maxdepth 1 -mindepth 1 -type f -printf "%f*%s\\n" | sort'
        folders = f'find {d} -maxdepth 1 -mindepth 1 -type d -not -path "./" -printf "%f\\n" | sort'
        return self.run(f'{folders} && {files}')
    
    def remove(self, path:str, *items:list[str], rf=True):
        full_paths = [f"{self.workspace.path}/{path}/{i}" for i in items]
        return self.run(f"rm{' -rf ' if rf else ' '}{' '.join(full_paths)}")
    
    def remove_jobs(self, jobs:List[Job]):
        full_paths = [f"{self.workspace.path}/{job.share}/hlrs/{job.name}" for job in jobs]
        return self.run(f"rm -rf {' '.join(full_paths)}")
    
    def submit_jobs(self, jobs:List[Job]):
        commands = [
            f"{self.workspace.path}/{job.share}/hlrs/{job.name}/submit.sh {job.limit}"
            for job in jobs
        ]
        cmd = " && ".join(commands)
        print(cmd)
        return self.run(cmd)