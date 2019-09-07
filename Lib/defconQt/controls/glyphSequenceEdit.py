"""
The *glyphSequenceEdit* submodule
-----------------------------

The *glyphSequenceEdit* submodule provides a QLineEdit_ widget that besides its
text string can return a list of Glyph_ from the font specified in its
constructor.

.. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
.. _QLineEdit: http://doc.qt.io/qt-5/qlineedit.html
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QLineEdit

from defconQt.tools.textSplitter import splitText


def _glyphs(self):
    text = self.text()
    glyphNames = self.splitTextFunction(text, self._font.unicodeData)
    glyphs = [
        self._font[glyphName] for glyphName in glyphNames if glyphName in self._font
    ]
    return glyphs


class GlyphSequenceComboBox(QComboBox):
    splitTextFunction = staticmethod(splitText)

    def __init__(self, font, parent=None):
        super().__init__(parent)
        # setEditable(True) must be called before self.completer()
        # otherwise it will return None
        self.setEditable(True)
        completer = self.completer()
        completer.setCaseSensitivity(Qt.CaseSensitive)
        self.setCompleter(completer)
        self._font = font

    glyphs = _glyphs

    def text(self):
        return self.currentText()

    def setText(self, text):
        self.setEditText(text)


class GlyphSequenceEdit(QLineEdit):
    splitTextFunction = staticmethod(splitText)

    def __init__(self, font, parent=None):
        super().__init__(parent)
        self._font = font

    glyphs = _glyphs
