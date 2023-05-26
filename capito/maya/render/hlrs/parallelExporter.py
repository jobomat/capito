import sys
import pymel.core as pc

file_to_open = sys.argv[1]
filename = sys.argv[2]
startframe = int(sys.argv[3])
endframe = int(sys.argv[4])

pc.openFile(file_to_open, force=True)
pc.other.arnoldExportAss(
    f=f"{filename}_<RenderLayer>.ass",
    startFrame=startframe, endFrame=endframe
)