import sys
import pymel.core as pc

file_to_open = sys.argv[1]
filename = sys.argv[2]
startframe = int(sys.argv[3])
endframe = int(sys.argv[4])
rl_names = sys.argv[5].split(",")

pc.openFile(file_to_open, force=True)
render_layers = [l for l in pc.ls(type='renderLayer') if l.name() in rl_names]

for rl in render_layers:
    rl.setCurrent()
    pc.other.arnoldExportAss(
        f=f"{filename}_<RenderLayer>.ass",
        startFrame=startframe, endFrame=endframe,
        preserveReferences=True
    )