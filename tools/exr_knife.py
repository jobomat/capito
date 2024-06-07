import sys
from pathlib import Path
from subprocess import check_output
sys.path.append(str(Path().cwd().parent))

# from PySide2.QtWidgets import *
# from capito.core.ui.decorators import bind_to_host


# @bind_to_host
# class ExrKnife(QMainWindow):
#     def __init__(self, host: str=None, parent=None):
#         self._create_widgets()
#         self._connect_widgets()
#         self._create_layout()

#     def _create_widgets(self):
#         pass

#     def _connect_widgets(self):
#         pass

#     def _create_layout(self):
#         pass



OIIOTOOL = "C:/Program Files/Autodesk/Arnold/maya2024/bin/oiiotool.exe"
IMG = "N:/renderpal_testproject/images/aovs_with_different_drivers.0001.exr"
result = check_output([OIIOTOOL, "--info", "-v", IMG])
raw_channel_list = str(result).split(r"\r\n")[2].split(",")
channels = [c.replace("channel list:", "").strip() for c in raw_channel_list]
print([c for c in channels if c.startswith("crypto")])
print([c for c in channels if not c.startswith("crypto")])