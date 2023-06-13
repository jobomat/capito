from pathlib import Path

import paramiko


class Bridge:
    def __init__(self, bridge_server: str="141.62.110.225",
                 bridge_username: str="root", key_filename: str=None):
        #self.hlrs_user = hlrs_user
        self.bridge_server = bridge_server
        self.bridge_username = bridge_username
        self.bridgekeyfile = key_filename or r"K:\pipeline\hlrs\ca-hlrs.pub"
        self.ssh = self.ssh_connect()

    def ssh_connect(self):
        print("Trying to connect to HLRS...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            self.bridge_server, username=self.bridge_username,
            key_filename=self.bridgekeyfile,
            timeout=5
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
    
    def connection_established(self):
        out, err = self.cmd("connection_established")
        if err and not out:
            print("Connection could not be established.")
            return False
        return True
        
    def get_base_infos(self):
        out, err = self.cmd("get_base_infos")
        # print(f"get_base_infos: {out=}, {err=}")
        return eval(out[0].rstrip())
    
    def push_files(self, sync_file: str, ready_file: str):
        print("START rsync")
        print("Transfering...")
        out, err = self.cmd(f"push_files --syncfile /mnt{sync_file}")
        print("rsync out: ", out)
        print("rsync err: ", err)
        print("END rsync")
        if not err:
            o, e = self.cmd(f"ready_to_render --readyfile {ready_file}")
            print(o, e)
        return out
