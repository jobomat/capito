import contextlib
from enum import Enum
from pathlib import Path
import platform

from capito.haleres.settings import Settings


class JobStatus(Enum):
    ready_to_push = "ready_to_push"
    pushing = "pushing"
    ready_to_render = "ready_to_render"
    all_jobs_submitted = "all_jobs_submitted"
    paused = "paused"


class Job:
    def __init__(self, share:str, name:str, settings:Settings):
        self.share = share
        self.name = name
        self.settings = settings

        self.job_folders = {
            "scenes": "input/scenes",
            "jobs": "input/jobs",
            "images": "output/images",
            "logs": "output/logs",
            "status": "ipc/status",
            "rsync_push_logs": "ipc/rsync_pull_logs",
            "rsync_pull_logs": "ipc/rsync_push_logs",
            "submitted": "ipc/submitted",
            "images_expected": "ipc/images_expected",
            "images_rendering": "ipc/images_rendering",
            "images_rendered": "ipc/images_rendered",
            "logs_expected": "ipc/logs_expected"
        }
        
        if platform.system() == "Windows":
            self.base_path = Path(settings.share_to_letter(share)) / "hlrs_tests"
        else:
            self.base_path = Path(settings.mount_point) / share

    def create_job_folders(self):
        self.jobfolder = self.base_path / self.name
        self.jobfolder.mkdir(parents=True, exist_ok=True)
        for folder in self.job_folders.values():
            (self.jobfolder / folder).mkdir(parents=True, exist_ok=True)

    def status_file(self, status:JobStatus) -> Path:
        return self.jobfolder / self.job_folders["status"] / status.value
    
    def get_status(self, status:JobStatus) -> bool:
        return self.status_file(status).exists()
    
    def set_status(self, status:JobStatus, value):
        if value:
            self.status_file(status).touch()
        else:
            with contextlib.suppress(FileNotFoundError):
                self.status_file(status).unlink()

    def list_submitted_jobs(self):
        pass

    def list_unsubmitted_jobs(self):
        pass
    
    def list_rendered_images(self):
        pass

    def get_push_max(self):
        pass
    
    def get_push_progress(self):
        pass

    def get_submit_max(self):
        pass
    
    def get_submit_progress(self):
        pass
        
    def get_render_max(self):
        pass
    
    def get_render_progress(self):
        pass
        
    def get_pull_max(self):
        pass
    
    def get_pull_progress(self):
        pass