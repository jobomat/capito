import sys
from pathlib import Path
sys.path.append(str(Path().cwd().parent))

from capito.haleres.settings import Settings
from capito.haleres.ui.render_manager import RenderManager

s = Settings("K:/pipeline/hlrs/settings.json")
h = RenderManager(s)