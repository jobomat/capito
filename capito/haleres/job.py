import contextlib
from enum import Enum
from pathlib import Path
import platform

from capito.haleres.settings import Settings


class JobStatus(Enum):
    ready_to_push = "READY_TO_PUSH"
    pushing = "PUSHING"
    all_files_pushed = "ALL_FILES_PUSHED"
    ready_to_render = "READY_TO_RENDER"
    all_jobs_submitted = "ALL_JOBS_SUBMITTED"
    paused = "PAUSED"


class Job:
    """Represents a complete job packet for rendering at HLRS.
    Job packets are a collection of files and information
    not to confuse with the job files that will be submitted at HLRS.
    These job files are just one little part of job packets."""
    def __init__(self, share:str, name:str, settings:Settings):
        self.share = share
        self.name = name
        self.settings = settings

        # Altering job_folders dict may break backwards compatibility!
        self.job_folders = {
            "scenes": "input/scenes",
            "jobs": "input/jobs",
            "images": "output/images",
            "logs": "output/logs",
            "ipc": "ipc",
            "status": "ipc/status",
            "rsync": "ipc/rsync",
            "submitted": "ipc/submitted",
            "images_expected": "ipc/images_expected",
            "images_rendering": "ipc/images_rendering",
            "images_rendered": "ipc/images_rendered",
            "logs_expected": "ipc/logs_expected"
        }
        
        if platform.system() == "Windows":
            self.base_path = Path(settings.share_to_letter(share)) / "hlrs"
        else:
            self.base_path = Path(settings.mount_point) / share / "hlrs"
    
    @property
    def jobfolder(self) -> Path:
        return self.base_path / self.name
    
    @property
    def linked_files(self) -> Path:
        return self.get_folder("rsync") / "linked_files.txt"
    
    def exists(self):
        """Returns True if the jobfolder exists."""
        return self.jobfolder.exists()

    def get_linked_files_content(self):
        """If linked_files.txt exists, returns its content. Else empty string."""
        if not self.linked_files.exists():
            return ""
        return self.linked_files.read_text()
    
    def create_rsync_push_file(self):
        """Write a linux & rsync compatible file for rsync --files_from flag."""
        conformed_jobfolder = str(self.jobfolder).replace(':', ':\\')
        content = f"{self.get_linked_files_content()}\n{conformed_jobfolder}"
        linux_conformed_content = content.replace(
            self.settings.share_map[self.share], self.share
        ).replace("\\", "/")
        rsync_push_file = self.get_folder("rsync") / "files_to_push.txt"
        with open(str(rsync_push_file), mode="w", encoding="UTF-8", newline="\n") as f:
            f.write(linux_conformed_content)   
    
    def create_job_folders(self):
        """Create all job packet folders."""
        self.jobfolder.mkdir(parents=True, exist_ok=True)
        for folder in self.job_folders.values():
            (self.jobfolder / folder).mkdir(parents=True, exist_ok=True)

    def status_file(self, status:JobStatus) -> Path:
        """Returns the hypothetic path to a certain status file."""
        return self.jobfolder / self.job_folders["status"] / status.value
    
    def get_status(self, status:JobStatus) -> bool:
        """Returns True or False for the requestet JobStatus.
        This is determined by the existens of the status file in ipc/status folder."""
        return self.status_file(status).exists()
    
    def set_status(self, status:JobStatus, value):
        """Sets the given status according to the given value.
        This is done by creating or deleting the corresponding file in ipc/status."""
        if value:
            self.status_file(status).touch()
        else:
            with contextlib.suppress(FileNotFoundError):
                self.status_file(status).unlink()

    def get_folder(self, folder:str="") -> Path:
        """Get the full path to the requested folder."""
        return self.jobfolder / self.job_folders.get(folder, "")

    def __eq__(self, other: "Job") -> bool:
        return self.jobfolder == other.jobfolder