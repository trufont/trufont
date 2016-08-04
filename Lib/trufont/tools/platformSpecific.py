from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
import sys

# -----------
# File dialog
# -----------


def treatPackageAsFile():
    return sys.platform == "darwin"

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

# --------
# Menu bar
# --------


def useGlobalMenuBar():
    return sys.platform == "darwin"


def mergeOpenAndImport():
    return sys.platform == "darwin"


def windowCommandsInMenu():
    return sys.platform == "darwin"

# -------
# ToolBar
# -------


def useTabBar():
    return sys.platform == "darwin"

# -----------
# Message box
# -----------


def showAppIconInDialog():
    return sys.platform == "darwin"


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
