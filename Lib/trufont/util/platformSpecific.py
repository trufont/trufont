from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import sys

# -----------
# File dialog
# -----------
_ufoFileFormat = QApplication.translate("File dialog", "UFO Fonts {}")

if sys.platform == "darwin":
    fileFormats = _ufoFileFormat.format("(*.ufo)")
else:
    fileFormats = _ufoFileFormat.format("(metainfo.plist)")

# ---------
# Font size
# ---------

if sys.platform == "darwin":
    headerPointSize = 11
else:
    headerPointSize = 8

# ----
# Keys
# ----

if sys.platform == "darwin":
    deleteKey = Qt.Key_Backspace
else:
    deleteKey = Qt.Key_Delete
