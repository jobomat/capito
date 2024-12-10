import sys
from pathlib import Path
sys.path.append(str(Path().cwd().parent))
from capito.core.encoder.ui import SequenceEncoderUI

s = SequenceEncoderUI()