from pathlib import Path

import paramiko


DRIVE_MAP = {"cg1": "L:", "cg2": "M:", "cg3": "N:"}
MOUNT_MAP = {v: f"/{k}" for k, v in DRIVE_MAP.items()}


def create_rsync_list(filelist:list):
    rsync_list = []
    for f in filelist:
        f = f.replace("\\", "/")
        for letter, mount in MOUNT_MAP.items():
            f = f.replace(letter, mount)
        f = f.strip()
        if f:
            rsync_list.append(f)
    return rsync_list


def create_blender_jobfiles(ws_name: str, share_name: str, renderer:str, job_name:str, start:int, end:int, size:int):
    template_file = Path(__file__).parent / "renderer_templates" / f"{renderer}.sh"
    template = template_file.read_text(encoding="UTF-8")

    scene_folder = Path(share_name) / "hlrs" / job_name / "scenes"
    blend_files = list(scene_folder.glob("*.blend"))

    if not blend_files or len(blend_files) > 1:
        print("Please place exactly one *.blend file in the scenes folder.")
        print("Aborted.")
        return
    
    print("Writing job-files.")
    
    for i in range(start, end + 1, size):
        e = min(end, i+size-1)
        jobtext = template.format(
            job_name=job_name,
            workspace_name=ws_name,
            renderer=renderer,
            blender_file=blend_files[0].name,
            share_name=MOUNT_MAP[share_name].replace("/", ""),
            start_frame=i,
            end_frame=e
        )
        jobfile = Path(share_name) / "hlrs" / job_name / "jobs" / f"{job_name}_{i}_{e}.sh"
        jobfile.write_text(jobtext, encoding="UTF-8")
        



def create_job_files(ws_name: str, share_name: str, renderer:str, job_name:str, start:int, end:int, size:int):
    template = Path(__file__).parent / "renderer_templates" / f"{renderer}.sh"
    if not template.exists():
        print(f"No shell template for '{renderer}' found.")
        return
    if renderer.startswith("blender"):
        create_blender_jobfiles(ws_name, share_name, renderer, job_name, start, end, size)
    elif renderer.startswith("arnold"):
        print("arnold not implemented a.t.m. SORRY!")


class Bridge:
    def __init__(self, bridge_server: str="141.62.110.225",
                 bridge_username: str="root", key_filename: str=None):
        #self.hlrs_user = hlrs_user
        self.bridge_server = bridge_server
        self.bridge_username = bridge_username
        self.bridgekeyfile = key_filename or r"C:\Users\jobo\.ssh\ca-hlrs.pub"
        self.ssh = self.ssh_connect()

    def ssh_connect(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            self.bridge_server, username=self.bridge_username,
            key_filename=self.bridgekeyfile
        )
        return ssh
    
    def cmd(self, cmd: str):
        venv = "source ~/hlrs/bin/activate"
        cmd_script = "python ssh.py"
        cmd = cmd.replace("'", "")
        # print(f"{venv} && {cmd_script} {cmd}")
        i, o, e = self.ssh.exec_command(
            f"{venv} && {cmd_script} {cmd}"
        )
        return o.readlines(), e.readlines()
        
    def get_base_infos(self):
        out, err = self.cmd("get_base_infos")
        return eval(out[0].rstrip())
    
    def push_files(self, sync_file: str):
        print("START rsync")
        print("Transfering...")
        out, err = self.cmd(f"push_files --syncfile /mnt{sync_file}")
        print(out, err)
        print("END rsync")
        return out
