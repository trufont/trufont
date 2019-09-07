from PyQt5.QtCore import QMimeData


class GlyphsMimeData(QMimeData):
    def __init__(self):
        super().__init__()
        # we don't need to serialize until we want to do cross-app dnd
        self._glyphs = []

    def glyphs(self):
        return self._glyphs

    def setGlyphs(self, glyphs):
        self._glyphs = glyphs

    # ----------
    # Qt methods
    # ----------

    def formats(self):
        formats = super().formats()
        formats.append("text/plain")
        return formats

    def hasFormat(self, format_):
        if format_ == "text/plain":
            return True
        return super().hasFormat(format_)

    def retrieveData(self, mimeType, type_):
        if mimeType == "text/plain":
            return " ".join(glyph.name for glyph in self._glyphs)
        return super().retrieveData(mimeType, type_)
