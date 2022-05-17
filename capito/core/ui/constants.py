from pathlib import Path
import PySide2.QtCore
from PySide2.QtGui import QColor, QPalette, Qt


WHITE = QColor(255, 255, 255)
LIGHT = QColor(210, 210, 210)
BLACK = QColor(0, 0, 0)
RED = QColor(255, 0, 0)
PRIMARY = QColor(53, 53, 53)
SECONDARY = QColor(35, 35, 35)
TERTIARY = QColor(42, 130, 218)
DARK = QColor(20, 20, 20)
DISABLED_BG = QColor(45, 45, 45)
DISABLED_FG = QColor(75, 75, 75)

dark_palette = QPalette()

dark_palette.setColor(QPalette.Window,          PRIMARY)
dark_palette.setColor(QPalette.WindowText,      LIGHT)
dark_palette.setColor(QPalette.Base,            DARK)
dark_palette.setColor(QPalette.AlternateBase,   SECONDARY)
dark_palette.setColor(QPalette.ToolTipBase,     WHITE)
dark_palette.setColor(QPalette.ToolTipText,     WHITE)
dark_palette.setColor(QPalette.Text,            LIGHT)
dark_palette.setColor(QPalette.Button,          SECONDARY)
dark_palette.setColor(QPalette.ButtonText,      LIGHT)
dark_palette.setColor(QPalette.BrightText,      RED)
dark_palette.setColor(QPalette.Link,            TERTIARY)
dark_palette.setColor(QPalette.Highlight,       TERTIARY)
dark_palette.setColor(QPalette.HighlightedText, BLACK)
dark_palette.setColor(QPalette.Disabled, QPalette.Base, DISABLED_BG)
dark_palette.setColor(QPalette.Disabled, QPalette.Text, DISABLED_FG)
# dark_palette.setColor(QPalette.Active,)
# dark_palette.setColor(QPalette.Inactive,)
# dark_palette.setColor(QPalette.Normal, color)

ICON_PATH = Path(__file__).parent.parent.parent.parent / "resources" / "icons"

PySide2.QtCore.QDir.addSearchPath(
    'icons',
    str(ICON_PATH)
)

