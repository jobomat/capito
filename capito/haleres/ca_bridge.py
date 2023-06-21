from pathlib import Path
from subprocess import check_output, TimeoutExpired
import shlex
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
    def __init__(self, key:str=None, user:str=None, ip:str=None, interpreter:str=None, bridge:str=None):
        self.key = key or r"C:\Users\jobo\.ssh\ca-hlrs.pub"
        self.user = user or "root"
        self.ip = ip or "141.62.110.225"
        self.interpreter = interpreter or "/root/hlrs/bin/python"
        self.bridge = bridge or "/mnt/cg/pipeline/hlrs/haleres/bridge.py"

        self.ssh = ["ssh", "-i", self.key, f"{self.user}@{self.ip}", self.interpreter, self.bridge]
        self._workspace_path = None

    @property
    def workspace_path(self):
        if self._workspace_path is not None:
            return self._workspace_path
        self._workspace_path = self.hlrs_command(["workspace.path"])[0]
        return self._workspace_path

    def hdm_command(self, command):
        result = check_output(command, universal_newlines=True, shell=True)

    def hdm_subprocess(self, command, *args):
        ssh = local["ssh"]
        parameters = ["-i", self.key, f"{self.user}@{self.ip}", self.interpreter, command, *args]

        process = ssh.popen(parameters)
        try:
            process.communicate(timeout=1)
        except TimeoutExpired:
            pass

    def hlrs_command(self, commands:list):
        ssh_cmd = self.ssh + [shlex.quote(cmd) for cmd in commands]
        
        answer = check_output(ssh_cmd, universal_newlines=True, shell=True)   
        return eval(answer)
    
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
        
        source = self.workspace_path if direction == "pull" else "/mnt"
        target = "/mnt" if direction == "pull" else self.workspace_path

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
    

    