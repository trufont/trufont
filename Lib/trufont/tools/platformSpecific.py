from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication
import sys

# -----------
# File dialog
# -----------

_ufoFileFormat = QApplication.translate("File dialog", "UFO Fonts {}")

if sys.platform == "darwin":
    fileFormat = "(*.ufo)"
else:
    fileFormat = "(metainfo.plist)"

# -------------
# Key sequences
# -------------


def closeKeySequence():
    if sys.platform == "win32":
        return "Ctrl+W"
    return QKeySequence.Close

# -------
# ToolBar
# -------


def useTabBar():
    return sys.platform == "darwin"
