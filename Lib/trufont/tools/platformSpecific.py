from PyQt5.QtCore import Qt
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


def isDeleteEvent(event):
    if event.matches(QKeySequence.Delete):
        return True
    if sys.platform == "darwin" and event.key() == Qt.Key_Backspace:
        return True
    modifiers = event.modifiers()
    if modifiers & Qt.ShiftModifier or modifiers & Qt.AltModifier:
        modifiers_ = modifiers & ~Qt.ShiftModifier & ~Qt.AltModifier
        event_ = event.__class__(
            event.type(), event.key(), modifiers_,
            event.text(), event.isAutoRepeat(), event.count())
        return event_.matches(QKeySequence.Delete)
    return False

# -------
# Margins
# -------


def needsTighterMargins():
    return sys.platform == "darwin"

# -------
# ToolBar
# -------


def useTabBar():
    return sys.platform == "darwin"

# -----------
# Message box
# -----------


def useCenteredButtons():
    return sys.platform == "darwin"

# ----------
# Stylesheet
# ----------


def appStyleSheet():
    if sys.platform == "win32":
        return "QStatusBar::item { border: none; }"
    elif sys.platform == "darwin":
        return "QToolTip { background-color: white; }"
    return None
