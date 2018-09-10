import platform
import sys
import wx


def appNameAndStarInTitle():
    return sys.platform != "darwin"


def combinedModifiers():
    # on Windows, Ctrl+Alt is reserved by the system. use WinKey+Alt
    if sys.platform == "win32":
        return wx.MOD_META | wx.MOD_ALT
    return wx.MOD_CONTROL | wx.MOD_ALT


def customTitleBar():
    return False
    return sys.platform == "win32" and platform.win32_ver()[0] == "10"


def scaleModifier():
    if sys.platform == "darwin":
        return wx.MOD_ALT
    return wx.MOD_CONTROL


def translateCursor():
    # TODO: darwin
    # XXX: wx doesn't abstract properly here, in particular the
    # linux impl could use the new gtk3 cursors
    if sys.platform.startswith("linux"):
        return wx.CURSOR_SIZENESW
    return wx.CURSOR_SIZING


def typeSizeScale():
    # TODO: darwin
    if sys.platform.startswith("linux"):
        return 1.2
    return 1
