"""
The *platformSpecific* submodule
--------------------------------

While most of the time Qt abstracts any platform difference transparently,
there are times where it explicitly chooses not to (for instance, the Enter key
on Windows corresponds to the Return key on OSX) so to leave control to the
user.

All such occurrences are stored in the *platformSpecific* submodule to make
such code obvious and self-contained.

Fear not, these occurrences are rather anecdotic as you may tell from the size
of this file.
"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

# ------
# Colors
# ------


def colorOpacityMultiplier():
    """
    Returns a transparency multiplier to have consistent system colors on all
    platforms. Assumes Windows = 1.
    """
    if sys.platform == "darwin":
        return 1.4
    return 1


# -----
# Fonts
# -----


def fixedFont():
    """
    Returns a default fixed-pitch QFont_ for each supported platform.

    Returns "Consolas" instead of the default "Courier New" on Windows.

    TODO: test more

    .. _QFont: http://doc.qt.io/qt-5/qfont.html
    """
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    if sys.platform == "win32":
        # pick Consolas instead of Courier New
        font.setFamily("Consolas")
    elif sys.platform == "darwin":
        # pick Menlo instead of Monaco
        font.setFamily("Menlo")
        font.setPointSize(11)
    return font


def otherUIFont():
    """
    Returns an auxiliary UI font.
    """
    font = QFont()
    pointSize = 9
    if sys.platform == "win32":
        font.setFamily("Segoe UI")
    elif sys.platform == "darwin":
        try:
            platform
        except NameError:
            import platform
        if platform.mac_ver()[0].startswith("10.10"):
            font.setFamily("Lucida Grande")
        pointSize = 12
    elif sys.platform.startswith("linux"):
        font.setFamily("Luxi Sans")
    font.setPointSize(pointSize)
    return font


# ----
# Keys
# ----


def scaleModifier():
    if sys.platform == "darwin":
        return Qt.AltModifier
    return Qt.ControlModifier
