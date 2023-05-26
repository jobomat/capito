import sys
from pathlib import Path
sys.path.append(str(Path().cwd().parent))
from capito.core.hlrs.ui import HLRSConnectorUI
h = HLRSConnectorUI()