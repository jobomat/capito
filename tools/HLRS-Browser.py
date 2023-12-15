import sys
from pathlib import Path
sys.path.append(str(Path().cwd().parent))
from capito.haleres.settings import Settings
from capito.haleres.browser import HLRSBrowser
s = Settings("K:/pipeline/hlrs/settings.json")
h = HLRSBrowser(s)