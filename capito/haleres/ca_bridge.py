import os
from pathlib import Path
from subprocess import check_output, TimeoutExpired
import shlex
from typing import List
from uuid import uuid4

from plumbum import local


def format_file_size(file_size):
    file_size = int(file_size)
    units = ["bytes", "KB   ", "MB   ", "GB   "]
    unit_index = 0
    
    while file_size >= 1024 and unit_index < len(units) - 1:
        file_size /= 1024
        unit_index += 1
    
    return f"{file_size:.2f} {units[unit_index]}"


class CABridge:
    """Class to execute commands 
        - on the CA bridge linux-system (hdm_command method)
        - as well as on a HLRS login node. (hlrs_command method)
    To use it the user has to have the ssh pub key for the CA bridge in
    the user-home-dir/.ssh subfolder. The key must be named ca-hlrs.pub."""
    def __init__(self, settings):
        user_dir = os.path.expanduser('~').replace("\\", "/")
        self.key = f"{user_dir}/.ssh/ca-hlrs.pub"
        self.settings = settings

        self.hdm_ssh = [
            "ssh", "-i", self.key,
            f"{self.settings.bridge_user}@{self.settings.bridge_server}"
        ]
        self.hlrs_ssh = self.hdm_ssh + [self.settings.bridge_interpreter, self.settings.bridge_hlrs_caller]

    @property
    def workspace_path(self):
        if self.settings.workspace_path is None:
            workspace_path = self.hlrs_command(["workspace.path"])[0]
            workspace_name = self.hlrs_command(["workspace.name"])[0]
            self.settings.set_value("workspace_path", workspace_path)
            self.settings.set_value("workspace_name", workspace_name)
            self.settings.save()
        return self.settings.workspace_path
    
    @property
    def ca_shell_path(self) -> Path:
        return Path(__file__).parent / "ca_shell"
    
    @property
    def hlrs_full_qualified_path(self):
        return f"{self.settings.hlrs_user}@{self.settings.hlrs_server}:{self.workspace_path}"

    def hdm_command(self, command):
        return check_output(command, universal_newlines=True, shell=True)

    def hdm_subprocess(self, command, *args):
        ssh = local["ssh"]
        parameters = [
            "-i", self.key,
            f"{self.settings.bridge_user}@{self.settings.bridge_server}",
            self.settings.bridge_interpreter, command, *args
        ]
        process = ssh.popen(parameters)
        try:
            process.communicate(timeout=1)
        except TimeoutExpired:
            pass

    def hdm_execute_shell_template(self, template:str, **data):
        cmd = (self.ca_shell_path / template).read_text()
        cmd = cmd % data
        ssh_cmd = self.hdm_ssh + [cmd] 
        return self.hdm_command(ssh_cmd)
    
    def hdm_execute_shell_script(self, script_name:str, *args):
        ca_script = f"{self.settings.bridge_hlrs_caller[:-14]}ca_shell/{script_name}"
        ssh_cmd = self.hdm_ssh + [ca_script] + list(args)
        return self.hdm_command(ssh_cmd)
    
    def hlrs_command(self, commands:list):
        ssh_cmd = self.hlrs_ssh + [shlex.quote(cmd) for cmd in commands]      
        answer = check_output(ssh_cmd, universal_newlines=True, shell=True)   
        return eval(answer)
    
    def abort_push(self, share:str, jobname:str):
        self.hdm_execute_shell_script("kill_push.sh", share, jobname)
    
    def rsync(self, filelist:list, direction:str="pull"):
        share = filelist[1].split("/")
        filelist_text = "\n".join(filelist)
        id = uuid4()
        # TODO: Path beneath not very thoughtful... settings?
        communication_folder = Path(f"K:/pipeline/hlrs/rsync_communication/{id}")
        communication_folder.mkdir(mode=511, parents=True)
        from_file = communication_folder / "filelist.txt"
        with open(str(from_file), mode="w", encoding="UTF-8", newline="\n") as f:
            f.write(filelist_text)

        hlrs_full_qualified_path = f"zmcjbomm@hawk.hww.hlrs.de:{self.workspace_path}"
        
        source = hlrs_full_qualified_path if direction == "pull" else "/mnt"
        target = "/mnt" if direction == "pull" else hlrs_full_qualified_path

        # TODO: path from settings (?)        
        self.hdm_subprocess(
            "/mnt/cg/pipeline/capito/capito/haleres/rsync.py",
            source, target, f"/mnt/cg/pipeline/hlrs/rsync_communication/{id}"
        )

    def folder_listing(self, folder_name:str):
        answer = self.hlrs_command([f"folder_listing('{folder_name}')"])
        listing = {
            "folders":[],
            "files":[]
        }
        result = answer[0]
        current_folder = folder_name.split("/")[-1]
        if current_folder in result:
            result.remove(current_folder)
        for item in result:
            if "*" in item:
                name, size = item.split("*")
                listing["files"].append([name, format_file_size(size)])
            else:
                listing["folders"].append(item)
        return listing

    def list_job_folders(self):
        folders = []
        for share in self.settings.shares:
            folders.extend(self.folder_listing(f"{share}/hlrs")["folders"])
        return folders

    def get_current_running_jobs(self):
        return self.hlrs_command("get_current_running_jobs()")[0]

    def get_free_nodes(self):
        return self.settings.hlrs_node_limit - len(self.get_current_running_jobs())

    def get_pending_jobs(self):
        list_jobs_file = Path(__file__).parent / "sh_list_pending_jobs.template"
        cmd = list_jobs_file.read_text().replace("<WS_PATH>", self._workspace_path)

        job_list = {}
        for line in self.cmd(cmd):
            job, num = line.split(":")
            job_list[job] = int(num)

        return job_list
