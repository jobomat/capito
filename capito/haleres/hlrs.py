import os
from pathlib import Path
from subprocess import Popen, check_output, CalledProcessError
import time
from datetime import datetime
from typing import List

import paramiko


WS_LIST = "/opt/hlrs/non-spack/system/ws/1.4.0/bin/ws_list"
WS_FIND = "/opt/hlrs/non-spack/system/ws/1.4.0/bin/ws_find"
QSTAT = "/opt/hlrs/non-spack/system/wrappers/bin/qstat"


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


class HLRS:
    def __init__(self, 
                 login_server:str="hawk.hww.hlrs.de",
                 username:str="zmcjbomm"):
        self.login_server = login_server
        self.username = username
        self.mountpoint = "/mnt"

        self.workspace = None
        self.workspace_path = None

        if not vpn_running():
            vpn_start()
        self._ssh = self.ssh_connect()
        ws_list = self.list_workspaces()
        if ws_list:
            self.set_workspace(ws_list[0])

    def ssh_connect(self) -> paramiko.client.SSHClient:
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.login_server, username=self.username, timeout=5)
        return ssh
    
    def connection_established(self) -> bool:
        i, o, e = self._ssh.exec_command("pwd")
        if o.readlines() and not e.readlines():
            return True
        return False
    
    def _cmd(self, cmd: str) -> List[str]:
        i, o, e = self._ssh.exec_command(cmd)
        return [line.rstrip() for line in o.readlines()]
    
    def list_workspaces(self) -> List[str]:
        return [
            line.split(": ")[-1]
            for line in self._cmd(WS_LIST)
            if line.startswith("id: ")
        ]
        
    def get_workspace_path(self, workspace_name:str):
        result = self._cmd(f"{WS_FIND} {workspace_name}")
        return result[0]
    
    def set_workspace(self, workspace_name:str):
        self.workspace = workspace_name
        self.workspace_path = self.get_workspace_path(workspace_name)

    def qstat(self) -> list:
        return self._cmd(QSTAT)
    
    def ls(self, directory: str):
        return self._cmd(f"ls {directory}")

    def ls_workspace(self, directory: str=""):
        return self.ls(f"{self.workspace_path}/{directory}")
    
    def folder_listing(self, directory: str):
        return self._cmd(f"ls -l -g {self.workspace_path}/{directory}")
    
    def list_renderers(self):
        return self.ls(f"{self.workspace_path}/renderers")