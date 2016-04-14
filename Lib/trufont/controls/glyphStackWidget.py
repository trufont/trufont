from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QWidget


class GlyphStackWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alignment = "left"
        self._buffer = 15
        self._glyphs = []
        self._maxWidth = 300

        self._backgroundColor = Qt.transparent
        self._glyphColor = QColor.fromRgbF(0, 0, 0, .15)

        self._upm = 1000
        self._descender = -250

    # -------------
    # Notifications
    # -------------

    def _subscribeToGlyphs(self, glyphs):
        handledGlyphs = set()
        handledFonts = set()
        for glyph in glyphs:
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            font = glyph.font
            if font is None:
                continue
            if font in handledFonts:
                continue
            handledFonts.add(font)
            font.info.addObserver(self, "_fontChanged", "Info.Changed")

    def _unsubscribeFromGlyphs(self):
        handledGlyphs = set()
        handledFonts = set()
        for glyph in self._glyphs:
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.removeObserver(self, "Glyph.Changed")
            font = glyph.font
            if font is None:
                continue
            if font in handledFonts:
                continue
            handledFonts.add(font)
            font.info.removeObserver(self, "Info.Changed")

    def _glyphChanged(self, notification):
        self.update()

    def _fontChanged(self, notification):
        self.setGlyphs(self._glyphs)

    # --------------
    # Custom methods
    # --------------

    def glyphs(self):
        return self._glyphs

    def setGlyphs(self, glyphs):
        self._unsubscribeFromGlyphs()
        self._glyphs = glyphs
        upms = []
        descenders = []
        for glyph in self._glyphs:
            font = glyph.font
            if font is not None:
                upm = font.info.unitsPerEm
                if upm is not None:
                    upms.append(upm)
                descender = font.info.descender
                if descender is not None:
                    descenders.append(descender)
        if upms:
            self._upm = max(upms)
        if descenders:
            self._descender = min(descenders)
        if self._glyphs:
            self._maxWidth = max(glyph.width for glyph in self._glyphs)
        else:
            self._maxWidth = 300
        self._subscribeToGlyphs(glyphs)
        self.update()

    def alignment(self):
        return self._alignment

    def setAlignment(self, alignment):
        assert alignment in ("left", "center", "right")
        self._alignment = alignment
        self.update()

    def backgroundColor(self):
        return self._backgroundColor

    def setBackgroundColor(self, color):
        self._backgroundColor = color

    def glyphColor(self):
        return self._glyphColor

    def setGlyphColor(self, color):
        self._glyphColor = color

    # --------
    # Qt methods
    # --------

    def sizeHint(self):
        return QSize(330, 400)

    def paintEvent(self, event):
        rect = event.rect()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(rect, self._backgroundColor)
        if not self._glyphs:
            return

        painter.translate(0, self.height())
        painter.scale(1, -1)

        availableHeight = self.height() - 2 * self._buffer
        availableWidth = self.width() - 2 * self._buffer
        scale = availableHeight / (self._upm * 1.2)
        yOffset = abs(self._descender * scale) + self._buffer
        scale = min(scale, availableWidth / self._maxWidth)

        for glyph in self._glyphs:
            if self._alignment == "left":
                xOffset = self._buffer
            elif self._alignment == "center":
                xOffset = (self.width() - (glyph.width * scale)) / 2
            else:
                xOffset = availableWidth + self._buffer - glyph.width * scale
            path = glyph.getRepresentation("defconQt.QPainterPath")
            painter.save()
            painter.translate(xOffset, yOffset)
            painter.scale(scale, scale)
            painter.fillPath(path, self._glyphColor)
            painter.restore()
