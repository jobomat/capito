import contextlib
from enum import Enum
import json
from pathlib import Path
import platform
import shutil
from typing import List

from capito.haleres.settings import Settings
from capito.haleres.utils import count_lines, create_frame_tuple_list, replace
from capito.haleres.renderer import Renderer


class JobStatus(Enum):
    ready_to_push = "READY_TO_PUSH"
    pushing = "PUSHING"
    push_aborted = "PUSH_ABORTED"
    all_files_pushed = "ALL_FILES_PUSHED"
    pulling = "PULLING"
    all_files_pulled = "ALL_FILES_PULLED"
    ready_to_render = "READY_TO_RENDER"
    all_jobs_submitted = "ALL_JOBS_SUBMITTED"
    paused = "PAUSED"
    all_images_rendered = "ALL_IMAGES_RENDERED"
    finished = "FINISHED"


class Job:
    """Represents a complete job packet for rendering at HLRS.
    Job packets are a collection of files and information
    not to confuse with the job files that will be submitted at HLRS.
    These job files are just one little part of job packets.
    With this class one can create and monitor HLRS Renderjobs."""
    job_folders = {
        "input": "input",
        "output": "output",
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
        "logs_expected": "ipc/logs_expected",
        "stream_out": "ipc/streams/out",
        "stream_err": "ipc/streams/err",
        "pbs_ids": "ipc/pbs_ids",
    }
    # Altering job_folders dict may break backwards compatibility!
    
    def __init__(self, share:str, name:str, haleres_settings:Settings):
        if platform.system() == "Windows":
            self.base_path = Path(haleres_settings.share_to_letter(share)) / "hlrs"
        else:
            self.base_path = Path(haleres_settings.mount_point) / share / "hlrs"
        self.share = share
        self.name = name
        self.haleres_settings = haleres_settings

        self._renderer_file = self.jobfolder / "renderer.json"
        self._renderer:Renderer = None
        
        self._linked_files = []
        self._scene_files = []

        self._job_settings_file:Path = self.jobfolder / "job_settings.json"
        self._init_job_settings()

        self._num_jobs = None
        self._num_expected_renders = None

        self.remaining_jobs = 0
        self.limit = 0
    
    def __eq__(self, other: "Job") -> bool:
        return self.jobfolder == other.jobfolder

    @property
    def renderer(self):
        if not self._renderer:
            if self._renderer_file.exists():
                self._renderer = Renderer().from_json(str(self._renderer_file))
        return self._renderer
    
    @renderer.setter
    def renderer(self, renderer:Renderer):
        self._renderer = renderer
        self.save_renderer_config()

    @property
    def framelist(self):
        return self.job_settings["framelist"]
    
    @framelist.setter
    def framelist(self, framelist:str):
        self.job_settings["framelist"] = framelist
        self.save_job_settings()
    
    @property
    def jobsize(self):
        return self.job_settings["jobsize"]
    
    @jobsize.setter
    def jobsize(self, jobsize:int):
        self.job_settings["jobsize"] = int(jobsize)
        self.save_job_settings()
    
    @property
    def frame_padding(self):
        return self.job_settings["frame_padding"]
    
    @frame_padding.setter
    def frame_padding(self, frame_padding:int):
        self.job_settings["frame_padding"] = frame_padding
        self.save_job_settings()
    
    @property
    def walltime_minutes(self):
        return self.job_settings["walltime_minutes"]
    
    @walltime_minutes.setter
    def walltime_minutes(self, walltime_minutes:int):
        self.job_settings["walltime_minutes"] = int(walltime_minutes)
        self.save_job_settings()
    
    @property
    def jobfolder(self) -> Path:
        return self.base_path / self.name
    
    @property
    def linked_files(self) -> List[str]:
        if self._linked_files:
            return self._linked_files
        linked_files_file = self.get_folder("rsync") / "linked_files.txt"
        if not linked_files_file.exists():
            linked_files_file.touch()
            return []
        return linked_files_file.read_text().strip().split("\n")
    
    @linked_files.setter
    def linked_files(self, file_list:List[str]):
        self._linked_files = file_list
        linked_files_file = self.get_folder("rsync") / "linked_files.txt"
        linked_files_file.write_text("\n".join(self._linked_files))

    @property
    def scene_files(self):
        return list((self.jobfolder / self.job_folders["scenes"]).glob("*"))

    def save_renderer_config(self):
        if not self._renderer:
            print("Can't save renderer config as no renderer was specified.")
            return
        self._renderer.save_json(str(self._renderer_file))
    
    def save_job_settings(self):
        self._job_settings_file.write_text(json.dumps(self.job_settings, indent=4))
    
    def exists(self) -> bool:
        """Returns True if the jobfolder exists.

        Returns:
            bool: True if jobfolder exists else False
        """
        return self.jobfolder.exists()
    
    def create_job_folders(self) -> None:
        """Create all job packet folders plus sumbit script."""
        self.jobfolder.mkdir(parents=True, exist_ok=True)
        for folder in self.job_folders.values():
            (self.jobfolder / folder).mkdir(parents=True, exist_ok=True)

        submitter_source = Path(__file__).parent / "hlrs_shell" / "submit.sh"
        submitter_dest = self.jobfolder / "submit.sh"
        print(submitter_source, submitter_dest)
        shutil.copy(submitter_source, submitter_dest)

    def write_job_files(self) -> None:
        """write the jobfiles.sh for PBS Rendering at HLRS
        """
        self._purge_folder("jobs")
        per_job_string = ""
        replacement_dict = self._get_replacement_dict()
        scene_files = self.scene_files
        framelist = f"1-{len(scene_files)}" if self.renderer.single_frame_renderer else self.framelist
        tuple_list = create_frame_tuple_list(framelist, self.jobsize)

        i = 0
        for start, end in tuple_list:
            per_frame_list = []
            for frame in range(start, end + 1):
                image_name = f"{scene_files[0].name}.{str(frame).zfill(self.frame_padding)}"
                per_frame_rpd = {
                    **replacement_dict,
                    **self.renderer.get_flag_lookup_dict(),
                    "padded_frame_number": str(frame).zfill(self.frame_padding)
                }
                if self.renderer.single_frame_renderer:
                    # Hacky. Maybe better overall design could fix this
                    per_frame_rpd["scenefile_name"] = scene_files[i].name
                    per_frame_rpd["jobfile_name"] = scene_files[i].stem
                    image_name = scene_files[i].stem
                i += 1
                per_frame_string = self.renderer.get_per_frame_string()
                per_frame_list.append(replace(per_frame_string, per_frame_rpd))
                (Path(self.get_folder("images_expected")) / image_name).touch()
        
            per_job_rpd = {
                **replacement_dict,
                **self.renderer.get_flag_lookup_dict(),
                "start_frame": start,
                "end_frame": end,
                "jobfile_name": self._get_jobfile_name(start, end),
                "scenefile_name": scene_files[0].name,
                "per_frame": "\n".join(per_frame_list),
            }
            per_job_string = self.renderer.get_per_job_string()
            per_job_string = replace(per_job_string, per_job_rpd)
            
            job_file = self.get_folder("jobs") / f"{per_job_rpd['jobfile_name']}.sh"
            with open(str(job_file), mode="w", encoding="UTF-8", newline="\n") as jf:
                jf.write(per_job_string)

    def create_rsync_push_file(self) -> None:
        """Write a linux & rsync compatible file for rsync --files_from flag."""
        conformed_jobfolder = str(self.jobfolder).replace(':', ':\\')
        content = "\n".join(self.linked_files + [conformed_jobfolder])
        print(content)
        linux_conformed_content = content.replace(
            self.haleres_settings.share_map[self.share], self.share
        ).replace("\\", "/").strip()
        rsync_push_file = self.get_folder("rsync") / "files_to_push.txt"
        with open(str(rsync_push_file), mode="w", encoding="UTF-8", newline="\n") as f:
            f.write(linux_conformed_content)

    def write_pathmap_json(self):
        """Writing a generic pathmap for the defined shares."""
        pm = {f"{l}/": f"{self.haleres_settings.workspace_path}/{s}/" for s, l in self.haleres_settings.share_map.items()}
        pathmap = {"linux": pm}
        with (self.get_folder("input") / "pathmap.json").open("w") as pmf:
            json.dump(pathmap, pmf)

    def get_status(self, status:JobStatus) -> bool:
        """Returns True or False for the requestet JobStatus.
        This is determined by the existens of the status file in ipc/status folder."""
        return self._status_file(status).exists()
    
    def set_status(self, status:JobStatus, value):
        """Sets the given status according to the given value.
        This is done by creating or deleting the corresponding file in ipc/status."""
        if value:
            self._status_file(status).touch()
        else:
            with contextlib.suppress(FileNotFoundError):
                self._status_file(status).unlink()

    def is_active(self):
        inactive_states = (
            self.is_finished(),
            self.is_paused(),
            not self.is_ready_to_push()
        )
        return not any(inactive_states)

    def is_ready_to_push(self):
        return self.get_status(JobStatus.ready_to_push)

    def is_pushing(self):
        return self.get_status(JobStatus.pushing)
    
    def is_pulling(self):
        return self.get_status(JobStatus.pulling)
    
    def is_ready_to_render(self):
        return self.get_status(JobStatus.ready_to_render)

    def is_paused(self):
        return self.get_status(JobStatus.paused)

    def is_finished(self):
        return self.get_status(JobStatus.finished)
    
    def set_paused(self, paused:bool):
        self.set_status(JobStatus.paused, paused)
    
    def set_ready_to_push(self, ready:bool):
        self.set_status(JobStatus.ready_to_push, ready)
    
    def all_files_pushed(self):
        return self.get_status(JobStatus.all_files_pushed)

    def get_folder(self, folder:str="") -> Path:
        """Get the full path to the requested folder."""
        return self.jobfolder / self.job_folders.get(folder, "")
    
    def get_relative_path(self, folder:str="") -> str:
        return f"{self.share}/hlrs/{self.name}/{self.job_folders.get(folder, '')}"
    
    def get_hlrs_folder(self, folder:str="") -> str:
        return f"{self.haleres_settings.workspace_path}/{self.get_relative_path(folder)}"
    
    def get_files_to_pull(self):
        local_images = [
            img.stem for img in list(self.get_folder("images").glob("*"))
        ]
        remote_images = [
            img for img in list(self.get_folder("images_rendered").glob("*"))
        ]
        files_to_pull = [
            f"{self.get_relative_path('images')}/{img.name}" for img in remote_images if img.stem not in local_images
        ]
        files_to_pull.append(self.get_relative_path("logs"))
        return files_to_pull
    
    def write_pull_file(self):
        pullfile = self.get_folder("rsync") / "files_to_pull.txt"
        pullfile.write_text("\n".join(self.get_files_to_pull()))

    def are_files_to_pull(self):
        num_local_images = len(list(self.get_folder("images").glob("*")))
        num_remote_images = len(list(self.get_folder("images_rendered").glob("*")))
        return num_local_images < num_remote_images
    
    def update_status(self):
        if self.is_ready_to_render() and (self.num_expected_renders() == self.num_pulled()):
            self.set_status(JobStatus.all_files_pulled, True)
            self.set_status(JobStatus.finished, True)

    def get_push_max(self):
        """Percentage... see get_push_progress() down below."""
        return 100
        
    def get_push_progress(self):
        """rsync push progress is hard to estimate.
        So we fall back to % of lines in a log file vs a dryrun logfile."""
        if self.get_status(JobStatus.all_files_pushed):
            return 100
        if self.get_status(JobStatus.pushing):
            ipc_dir = self.get_folder('rsync')
            dry_log = ipc_dir / "pushlog_dryrun.log"
            real_log = ipc_dir / "pushlog.log"
            if dry_log.exists() and real_log.exists():
                return count_lines(real_log) / (count_lines(dry_log) + 3) * 100
        return 0
    
    def num_unsubmitted_jobs(self):
        if self.is_finished():
            return 0
        return self.num_jobs() - self.num_submitted_jobs()
    
    def num_jobs(self):
        """Total number of generated jobfiles."""
        if not self._num_jobs:
            self._num_jobs = sum(1 for _ in self.get_folder('jobs').glob("*.sh"))
        return self._num_jobs
        
    def num_submitted_jobs(self):
        """Jobfiles that already are submitted."""
        if self.get_status(JobStatus.all_jobs_submitted):
            return self.num_jobs()
        return sum(1 for _ in self.get_folder('submitted').glob("*.sh"))

    def num_expected_renders(self):
        """Number of expected rendered images."""
        if not self._num_expected_renders:
            self._num_expected_renders = sum(1 for _ in self.get_folder('images_expected').glob("*"))
        return self._num_expected_renders
    
    def num_rendered(self):
        """Number of already rendered images."""
        if self.get_status(JobStatus.all_images_rendered):
            return self._num_expected_renders()
        return sum(1 for _ in self.get_folder('images_rendered').glob("*"))
    
    def num_rendering(self):
        """Number of already rendered images."""
        if self.get_status(JobStatus.all_images_rendered):
            return self._num_expected_renders()
        return sum(1 for _ in self.get_folder('images_rendering').glob("*"))

    def num_expected_pulls(self):
        """As the images will be the bulk of data to pull we resort to number of images here."""
        return self.num_expected_renders()

    def num_pulled(self):
        """Number of already pulled images."""
        if self.get_status(JobStatus.finished):
            return self.num_expected_pulls()
        return sum(1 for _ in self.get_folder('images').glob("*"))

    def _purge_folder(self, folder:str):
        if self.job_folders.get(folder, False):
            for file in self.get_folder(folder).glob("*"):
                file.unlink()
    
    def _init_job_settings(self):
        if self._job_settings_file.exists():
            self.job_settings = json.loads(self._job_settings_file.read_text())
        else:
            self.job_settings = {"framelist": "", "jobsize": 1, "frame_padding": 4, "walltime_minutes": 20}
            self._job_settings_file.parent.mkdir(exist_ok=True)
            self.save_job_settings()

    def _get_replacement_dict(self) -> dict:
        """Get the key value pairs, that are needed 
        for per job and per frame replacements when creating jobfiles."""
        return {
            "job_name": self.name,
            "share_name": self.share,
            "frame_padding_hashes": "#" * self.frame_padding,
            "walltime_minutes": self.walltime_minutes,
            "workspace_name": self.haleres_settings.workspace_name
        }

    def _get_jobfile_name(self, start, end):
        """Create a jobfilename depending on jobsize:
        If only one frame is rendered only one number will be added.
        Otherwise start and end frame will be added."""
        return f"{self.name}_{start}" if start == end else f"{self.name}_{str(start).zfill(4)}_{str(end).zfill(4)}"
    
    def _status_file(self, status:JobStatus) -> Path:
        """Returns the hypothetic path to a certain status file."""
        return self.jobfolder / self.job_folders["status"] / status.value
    

class JobProvider:
    def __init__(self, settings:Settings):
        self.settings = settings
        self.jobs:List[Job] = []
        self.job_map = {}
        self.reload_all_jobs()

    def reload_all_jobs(self):
        self.jobs = []
        counter = 0
        for letter, share in self.settings.letter_map.items():
            hlrs_folder = list(Path(self._base(letter, share)).glob("hlrs"))
            if hlrs_folder:
                for job_folder in hlrs_folder[0].glob("*"):
                    j = Job(share, job_folder.name, self.settings)
                    self.jobs.append(j)
                    self.job_map[f"{share}/{job_folder.name}"] = counter
                    counter += 1

    def get_job(self, share, name):
        key = f"{share}/{name}"
        index = self.job_map.get(key, None)
        if index is None:
            return None
        return self.jobs[index]

    def calculate_submit_limits(self, free_nodes: int) -> List[Job]:
        """get a list of jobs with currently appropriate submit limits."""
        jobs_with_pending_jobs = [
            job for job in self.jobs
            if not job.is_finished() and job.is_ready_to_render() and not job.is_paused()
        ]
        for job in jobs_with_pending_jobs:
            job.remaining_jobs = job.num_unsubmitted_jobs()
            job.limit = 0
        num_pending_jobs = sum([job.remaining_jobs for job in jobs_with_pending_jobs])
        # print(f"{num_pending_jobs=}")

        while free_nodes > 0 and num_pending_jobs > 0:
            num_jobs = sum(job.remaining_jobs != 0 for job in jobs_with_pending_jobs)
            even_share = int(free_nodes / num_jobs)
            for job in jobs_with_pending_jobs:
                chunk = min(job.remaining_jobs, even_share, free_nodes)
                job.limit += chunk
                job.remaining_jobs -= chunk
                free_nodes -= chunk
                num_pending_jobs -= chunk

        return [job for job in jobs_with_pending_jobs if job.limit > 0]
    
    def get_jobs_to_push(self):
        return [
            job for job in self.jobs
            if job.is_ready_to_push()
            and not job.is_pushing()
            and not job.all_files_pushed()
            and not job.is_paused()
        ]
    
    def get_unfinished_jobs(self):
        for job in self.jobs:
            job.update_status()
        return [job for job in self.jobs if not job.is_finished()]

    def _base(self, letter, share):
        """Get platformspecific variant of base path (letter or share name)"""
        if platform.system() == "Windows":
            return letter
        else:
            return f"{self.settings.mount_point}/{share}"