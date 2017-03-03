from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
import os
import sys

# -----------
# File dialog
# -----------


def treatPackageAsFile():
    return sys.platform == "darwin"

# -----
# Fonts
# -----


def fontSizeDelta():
    return int(sys.platform == "darwin")

# -------------
# Key sequences
# -------------


def altDeleteSequence():
    if sys.platform == "darwin":
        return "Backspace"
    return None

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
    if sys.platform == "darwin":
        return True
    elif sys.platform.startswith("linux"):
        env = os.environ
        if env.get("XDG_CURRENT_DESKTOP") == "Unity" and \
                len(env.get("UBUNTU_MENUPROXY", "")) > 1:
            return True
    return False


def mergeOpenAndImport():
    return sys.platform == "darwin"


def windowCommandsInMenu():
    return sys.platform == "darwin"

# -----------
# Main window
# -----------


def appNameInTitle():
    if sys.platform == "darwin":
        return False
    return True


def shouldSpawnDocument():
    return sys.platform != "darwin"

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


# ----------
# Stylesheet
# ----------


def appStyleSheet():
    if sys.platform == "win32":
        return "QStatusBar::item { border: none; } QWidget { \
            font-family: 'Segoe UI', sans-serif; font-size: 9pt; }"
    elif sys.platform == "darwin":
        return "QToolTip { background-color: white; }"
    return None
