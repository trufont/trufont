"""
The *glyphNameComboBox* submodule
-----------------------------

The *glyphNameComboBox* submodule provides a QComboBox_ widget that performs
autocompletion from a Font_’s glyph names.

.. _Font: http://ts-defcon.readthedocs.org/en/ufo3/objects/font.html
.. _QComboBox: http://doc.qt.io/qt-5/qcombobox.html
"""

from PyQt5.QtCore import QStringListModel
from PyQt5.QtWidgets import QComboBox, QCompleter

from defconQt.tools.textSplitter import splitText

__all__ = ["GlyphNameComboBox"]


class GlyphNameCompleter(QCompleter):
    def __init__(self, font, parent=None):
        super().__init__(parent)
        self._font = font
        self.setCompletionMode(QCompleter.InlineCompletion)

    def splitPath(self, path):
        # hack around the splitPath() function to feed custom results to the
        # QCompleter, see: http://stackoverflow.com/a/28286322/2037879
        match, replace = _search(path, self._font)
        if replace:
            comboBox = self.widget()
            comboBox.setCurrentText(match)
            comboBox.lineEdit().selectAll()
            match = None
        if match is None:
            model = QStringListModel()
        else:
            model = QStringListModel([match])
        self.setModel(model)
        return [path]


class GlyphNameComboBox(QComboBox):
    """
    # TODO: consider popup completer or adding font glyph names?
    """

    splitTextFunction = splitText

    def __init__(self, font, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        completer = GlyphNameCompleter(font)
        self.setCompleter(completer)


def _search(text, font):
    # no text
    if not text:
        return None, False
    glyphNames = font.keys()
    match = None
    # direct match
    if text in glyphNames:
        match = text
    # character entry
    elif len(text) == 1:
        uniValue = ord(text)
        gName = font.unicodeData.glyphNameForUnicode(uniValue)
        if gName is not None:
            return gName, True
    # fallback. find closest match
    if not match:
        for glyphName in sorted(glyphNames):
            if glyphName.startswith(text):
                match = glyphName
                break
    return match, False
