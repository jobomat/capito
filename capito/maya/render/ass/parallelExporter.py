import shutil
import sys
from pathlib import Path

import pymel.core as pc

file_to_open = sys.argv[1]
startframe = int(sys.argv[2])
endframe = int(sys.argv[3])
rl_names = sys.argv[4].split(",")
temp_export_dir = sys.argv[5]
job_name = sys.argv[6]
job_share = sys.argv[7]
temp_status_dir = Path(sys.argv[8])
num_exports_total = int(sys.argv[9])
capito_base_dir = sys.argv[10]
haleres_settings_file = sys.argv[11]

pc.openFile(file_to_open, force=True)
render_layers = [l for l in pc.ls(type='renderLayer') if l.name() in rl_names]

# first export the specified frames...
for rl in render_layers:
    rl.setCurrent()
    pc.other.arnoldExportAss(
        f=f"{temp_export_dir}/{job_name}_<RenderLayer>.ass",
        startFrame=startframe, endFrame=endframe,
        preserveReferences=True
    )
    for i in range(startframe, endframe + 1):
        (temp_status_dir / f"{job_name}_{rl.name()}_{i}").touch()

# ...then only if all images have been written
# copy them back in one go to reduce network bandwidth competition
if num_exports_total == len(list(temp_status_dir.glob("*"))):
    sys.path.append(capito_base_dir)

    from capito.haleres.settings import Settings
    from capito.haleres.job import Job

    settings = Settings(haleres_settings_file)
    job = Job(job_share, job_name, settings)

    for file in Path(temp_export_dir).glob("*"):
        shutil.move(str(file), str(job.get_folder("scenes") / file.name))
    
    job.write_job_files()
    job.set_ready_to_push(True)
    
    try:
        for file in temp_status_dir.glob("*"):
            file.unlink()
        temp_status_dir.rmdir()
        Path(temp_export_dir).rmdir()
        temp_status_dir.parent.rmdir()
    except:
        pass
