from collections import Iterable
from defcon import Color
from defconQt.tools.drawing import colorToQColor
from PyQt5.QtCore import QByteArray, QSettings
from PyQt5.QtGui import QColor

_metricsWindowComboBoxItems = [
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "0123456789",
    "nn/? nono/? oo",
    "HH/? HOHO/? OO"
]

_latinDefaultName = "Latin-default"

_latinDefaultGlyphNames = \
    ["space", "exclam", "quotesingle", "quotedbl", "numbersign", "dollar",
     "percent", "ampersand", "parenleft", "parenright", "asterisk", "plus",
     "comma", "hyphen", "period", "slash", "zero", "one", "two", "three",
     "four", "five", "six", "seven", "eight", "nine", "colon", "semicolon",
     "less", "equal", "greater", "question", "at", "A", "B", "C", "D", "E",
     "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S",
     "T", "U", "V", "W", "X", "Y", "Z", "bracketleft", "backslash",
     "bracketright", "asciicircum", "underscore", "grave", "a", "b", "c", "d",
     "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
     "t", "u", "v", "w", "x", "y", "z", "braceleft", "bar", "braceright",
     "asciitilde", "exclamdown", "cent", "sterling", "currency", "yen",
     "brokenbar", "section", "copyright", "ordfeminine", "guillemotleft",
     "logicalnot", "registered", "macron", "degree", "plusminus",
     "twosuperior", "threesuperior", "mu", "paragraph", "periodcentered",
     "onesuperior", "ordmasculine", "guillemotright", "onequarter", "onehalf",
     "threequarters", "questiondown", "Agrave", "Aacute", "Acircumflex",
     "Atilde", "Adieresis", "Aring", "AE", "Ccedilla", "Egrave", "Eacute",
     "Ecircumflex", "Edieresis", "Igrave", "Iacute", "Icircumflex",
     "Idieresis", "Eth", "Ntilde", "Ograve", "Oacute", "Ocircumflex",
     "Otilde", "Odieresis", "multiply", "Oslash", "Ugrave", "Uacute",
     "Ucircumflex", "Udieresis", "Yacute", "Thorn", "germandbls", "agrave",
     "aacute", "acircumflex", "atilde", "adieresis", "aring", "ae", "ccedilla",
     "egrave", "eacute", "ecircumflex", "edieresis", "igrave", "iacute",
     "icircumflex", "idieresis", "eth", "ntilde", "ograve", "oacute",
     "ocircumflex", "otilde", "odieresis", "divide", "oslash", "ugrave",
     "uacute", "ucircumflex", "udieresis", "yacute", "thorn", "ydieresis",
     "dotlessi", "gravecomb", "acutecomb", "uni0302", "uni0308", "uni030A",
     "tildecomb", "uni0327", "quoteleft", "quoteright", "minus"]

_fallbackValues = {
    "fontWindow/glyphCellSize": 68,
    "metricsWindow/comboBoxItems": _metricsWindowComboBoxItems,
    "misc/loadRecentFile": False,
    "outputWindow/wrapLines": False,
    "scriptingWindow/hSplitterSizes": [0, 1],
    "scriptingWindow/vSplitterSizes": [1, 100],
    "settings/defaultGlyphSet": _latinDefaultName,
}

# --------------------------
# Generic get/set + fallback
# --------------------------

_type = type


def value(key, fallback=None, type=None):
    settings = QSettings()
    if fallback is None and key in _fallbackValues:
        fallback = _fallbackValues[key]
        if isinstance(fallback, Iterable):
            type = _type(fallback[0])
        else:
            type = _type(fallback)
    return settings.value(key, fallback, type)


def setValue(key, value):
    settings = QSettings()
    settings.setValue(key, value)

# -----------
# Convenience
# -----------

# value

# XXX: use more robust setting
# defaultGlyphSet will always be the first in array and we have a bool
# to say whether we should apply it


def fontWindowGeometry():
    return value("fontWindow/geometry", type=QByteArray)


def setFontWindowGeometry(geometry):
    setValue("fontWindow/geometry", geometry)


def fontFeaturesWindowGeometry():
    return value("fontFeaturesWindow/geometry", type=QByteArray)


def setFontFeaturesWindowGeometry(geometry):
    setValue("fontFeaturesWindow/geometry", geometry)


def fontInfoWindowGeometry():
    return value("fontInfoWindow/geometry", type=QByteArray)


def setFontInfoWindowGeometry(geometry):
    setValue("fontInfoWindow/geometry", geometry)


def glyphCellSize():
    return value("fontWindow/glyphCellSize")


def setGlyphCellSize(cellSize):
    setValue("fontWindow/glyphCellSize", cellSize)


def glyphWindowGeometry():
    return value("glyphWindow/geometry", type=QByteArray)


def setGlyphWindowGeometry(geometry):
    setValue("glyphWindow/geometry", geometry)


def groupsWindowGeometry():
    return value("groupsWindow/geometry", type=QByteArray)


def setGroupsWindowGeometry(geometry):
    setValue("groupsWindow/geometry", geometry)


def inspectorWindowGeometry():
    return value("inspectorWindow/geometry", type=QByteArray)


def setInspectorWindowGeometry(geometry):
    setValue("inspectorWindow/geometry", geometry)


def metricsWindowGeometry():
    return value("metricsWindow/geometry", type=QByteArray)


def setMetricsWindowGeometry(geometry):
    setValue("metricsWindow/geometry", geometry)


def outputWindowGeometry():
    return value("outputWindow/geometry", type=QByteArray)


def setOutputWindowGeometry(geometry):
    setValue("outputWindow/geometry", geometry)


def outputWindowWrapLines():
    return value("outputWindow/wrapLines")


def setOutputWindowWrapLines(value):
    setValue("outputWindow/wrapLines", value)


def scriptingWindowGeometry():
    return value("scriptingWindow/geometry", type=QByteArray)


def setScriptingWindowGeometry(geometry):
    setValue("scriptingWindow/geometry", geometry)


def scriptingWindowHSplitterSizes():
    return value("scriptingWindow/hSplitterSizes")


def setScriptingWindowHSplitterSizes(sizes):
    setValue("scriptingWindow/hSplitterSizes", sizes)


def scriptingWindowVSplitterSizes():
    return value("scriptingWindow/vSplitterSizes", type=int)


def setScriptingWindowVSplitterSizes(sizes):
    setValue("scriptingWindow/vSplitterSizes", sizes)


def settingsWindowGeometry():
    return value("settingsWindow/geometry", type=QByteArray)


def setSettingsWindowGeometry(geometry):
    setValue("settingsWindow/geometry", geometry)


def defaultGlyphSet():
    return value("settings/defaultGlyphSet")


def setDefaultGlyphSet(name):
    if name is None:
        name = ""
    setValue("settings/defaultGlyphSet", name)


def glyphListPath():
    return value("settings/glyphListPath", type=str)


def setGlyphListPath(path):
    if path is None:
        path = ""
    setValue("settings/glyphListPath", path)


def removeGlyphListPath(path):
    settings = QSettings()
    settings.remove("settings/glyphListPath")


def metricsWindowComboBoxItems():
    return value("metricsWindow/comboBoxItems")


def setMetricsWindowComboBoxItems(items):
    setValue("metricsWindow/comboBoxItems", items)


def importFileDialogState():
    return value("core/importFileDialogState", type=QByteArray)


def setImportFileDialogState(state):
    setValue("core/importFileDialogState", state)


def openFileDialogState():
    return value("core/openFileDialogState", type=QByteArray)


def setOpenFileDialogState(state):
    setValue("core/openFileDialogState", state)


def saveFileDialogState():
    return value("core/saveFileDialogState", type=QByteArray)


def setSaveFileDialogState(state):
    setValue("core/saveFileDialogState", state)


def exportFileDialogState():
    return value("core/exportFileDialogState", type=QByteArray)


def setExportFileDialogState(state):
    setValue("core/exportFileDialogState", state)


def scriptingFileDialogState():
    return value("scriptingWindow/fileDialogState", type=QByteArray)


def setScriptingFileDialogState(state):
    setValue("scriptingWindow/fileDialogState", state)


def loadRecentFile():
    return value("misc/loadRecentFile")


def setLoadRecentFile(value):
    setValue("misc/loadRecentFile", value)


def recentFiles():
    return value("core/recentFiles", [], type=str)


def setRecentFiles(recentFiles):
    setValue("core/recentFiles", recentFiles)

# containers


def readGlyphSets():
    settings = QSettings()
    size = settings.beginReadArray("glyphSets")
    glyphSets = {}
    if not size:
        glyphSets[_latinDefaultName] = _latinDefaultGlyphNames
    for i in range(size):
        settings.setArrayIndex(i)
        glyphSetName = settings.value("name", type=str)
        glyphSetGlyphNames = settings.value("glyphNames", type=str)
        glyphSets[glyphSetName] = glyphSetGlyphNames
    settings.endArray()
    return glyphSets


def writeGlyphSets(glyphSets):
    settings = QSettings()
    settings.beginWriteArray("glyphSets", len(glyphSets))
    index = 0
    for name, cset in glyphSets.items():
        settings.setArrayIndex(index)
        settings.setValue("name", name)
        settings.setValue("glyphNames", cset)
        index += 1
    settings.endArray()

# mark colors


def readMarkColors():
    settings = QSettings()
    size = settings.beginReadArray("misc/markColors")
    if not size:
        markColors = [
            [QColor(255, 0, 0), "Red"],
            [QColor(255, 255, 0), "Yellow"],
            [QColor(0, 255, 0), "Green"],
        ]
    else:
        markColors = []
    for i in range(size):
        settings.setArrayIndex(i)
        markColor = settings.value("color", type=str)
        markColorName = settings.value("name", type=str)
        markColors.append([colorToQColor(markColor), markColorName])
    settings.endArray()
    return markColors


def writeMarkColors(markColors):
    settings = QSettings()
    settings.beginWriteArray("misc/markColors")
    # serialized in UFO form
    i = 0
    for color, name in markColors:
        settings.setArrayIndex(i)
        settings.setValue("color", str(Color(color.getRgbF())))
        settings.setValue("name", name)
        i += 1
    settings.endArray()
