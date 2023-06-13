import json
import math
from pathlib import Path
import shutil


DRIVE_MAP = {"cg": "K:", "cg1": "L:", "cg2": "M:", "cg3": "N:"}
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


def create_job_folders(jobdir:Path):
    jobdir.mkdir()
    (jobdir / "jobs").mkdir()
    (jobdir / "scenes").mkdir()
    (jobdir / "output").mkdir()
    (jobdir / "logs").mkdir()
    (jobdir / "streams").mkdir()
    (jobdir / "transferable").mkdir()



def create_blender_jobfiles(ws_name: str, share_name: str, renderer:str, global_job_name:str, start:int, end:int, size:int):
    template_file = Path(__file__).parent / "renderer_templates" / f"{renderer}.sh"
    template = template_file.read_text(encoding="UTF-8")
    
    touch_template_file = Path(__file__).parent / "renderer_templates" / "blender_touch_snip.template.sh"
    touch_template = touch_template_file.read_text(encoding="UTF-8")

    scene_folder = Path(share_name) / "hlrs" / global_job_name / "scenes"
    blend_files = list(scene_folder.glob("*.blend"))
    share = MOUNT_MAP[share_name].replace("/", "")
    frame_padding = 4
    frame_padding_hashes = "#" * frame_padding

    if not blend_files or len(blend_files) > 1:
        print("Please save exactly one *.blend file in the scenes folder.")
        print("Aborted.")
        return
    
    print("Writing job-files.")

    jobfile_name = ""
    for i in range(start, end + 1, size):
        e = min(end, i+size-1)
        touch_snips = []
        for framenumber in range(i, e + 1):
            touch_snips.append(
                touch_template.format(
                    share_name=share,
                    global_job_name=global_job_name,
                    padded_framenumber=str(framenumber).zfill(frame_padding)
                )
            )
        jobfile_name = f"{global_job_name}_{i}_{e}"
        jobtext = template.format(
            global_job_name=global_job_name,
            workspace_name=ws_name,
            renderer=renderer,
            blender_file=blend_files[0].name,
            share_name=share,
            start_frame=i,
            end_frame=e,
            jobfile_name=jobfile_name,
            frame_padding_hashes=frame_padding_hashes,
            touch_snip="\n".join(touch_snips)
        )
        jobfile = Path(share_name) / "hlrs" / global_job_name / "jobs" / f"{jobfile_name}.sh"
        jobfile.write_text(jobtext, encoding="UTF-8")
    
    # submit_template_file = Path(__file__).parent / "submit.sh"
    # submit_template = submit_template_file.read_text(encoding="UTF-8")
    # submit_template = submit_template.replace("<<last_jobfile_without_extension>>", jobfile_name[:-3])
    # # NOT using file.write_text(...) here because 
    # # python 3.9 doesn't support the "newline" parameter for it.
    # # newline="\n" is needed to write a unix-style file for shell executability
    # with open(str(submit_template_file), mode="w", encoding="UTF-8", newline="\n") as f:
    #     f.write(submit_template)


def create_arnold_jobfiles(ws_name: str, ws_path:str, share_name: str, renderer:str, global_job_name:str, size:int):
    template_file = Path(__file__).parent / "renderer_templates" / f"{renderer}.sh"
    template = template_file.read_text(encoding="UTF-8")

    snip_template_file = Path(__file__).parent / "renderer_templates" / "arnold_kick_snip.template.sh"
    snip_template = snip_template_file.read_text(encoding="UTF-8")

    scene_folder = Path(share_name) / "hlrs" / global_job_name / "scenes"
    ass_files = list(scene_folder.glob("*.ass"))
    share = MOUNT_MAP[share_name].replace("/", "")

    filecounter = len(ass_files)

    print(f"{filecounter} ass-files detected in scenes folder.")
    print(f"Writing {math.ceil(filecounter / size)} job-files. ({size} renders per node)")

    jobcounter = 1

    while filecounter >= 0:
        kick_snip = ""
        for i in range(size):
            filecounter -= 1
            if filecounter < 0:
                break
            kick_snip += snip_template.format(
                share_name=share,
                job_name=global_job_name,
                ass_file=ass_files[filecounter].name,
                jobfile_name=ass_files[filecounter].stem
            )
        if not kick_snip:
            break
        jobfile_name = f"{global_job_name}_{str(jobcounter).zfill(4)}"
        jobtext = template.format(
            kick_snip=kick_snip,
            jobfile_name=jobfile_name,
            workspace_name=ws_name,
            renderer=renderer,
            share_name=share,
            job_name=global_job_name
        )
        jobfile = Path(share_name) / "hlrs" / global_job_name / "jobs" / f"{jobfile_name}.sh"
        jobfile.write_text(jobtext, encoding="UTF-8")
        jobcounter += 1
    
    pathmap = {
        "linux": {f"{letter}/": f"{ws_path}{path}/" for letter, path in MOUNT_MAP.items()}
    }
    pathmapfile = Path(share_name) / "hlrs" / global_job_name / "pathmap.json"
    with pathmapfile.open("w") as file:
        json.dump(pathmap, file)  # , indent=4)



def create_job_files(ws_name: str, ws_path:str, share_name: str, renderer:str, global_job_name:str, start:int, end:int, size:int):
    template = Path(__file__).parent / "renderer_templates" / f"{renderer}.sh"
    if not template.exists():
        print(f"No shell template for '{renderer}' found.")
        return
    if renderer.startswith("blender"):
        create_blender_jobfiles(ws_name, share_name, renderer, global_job_name, start, end, size)
    elif renderer.startswith("arnold"):
        create_arnold_jobfiles(ws_name, ws_path, share_name, renderer, global_job_name, size)

    submitter_source = Path(__file__).parent / "submit.sh"
    submitter_dest = Path(share_name) / "hlrs" / global_job_name / "submit.sh"

    shutil.copy(submitter_source, submitter_dest)