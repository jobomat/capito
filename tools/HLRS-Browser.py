import sys
from pathlib import Path
sys.path.append(str(Path().cwd().parent))
from capito.haleres.browser import HLRSBrowser
h = HLRSBrowser()