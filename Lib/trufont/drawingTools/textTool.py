from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtWidgets import QApplication
from defcon import LayoutEngine
from trufont.drawingTools.baseTool import BaseTool
import unicodedata

try:
    import compositor
except ImportError:
    compositor = None

_path = QPainterPath()
_path.moveTo(5.29, 17.96)
_path.lineTo(6.94, 17.96)
_path.lineTo(7.36, 21.5)
_path.lineTo(7.78, 21.95)
_path.lineTo(12.4, 21.95)
_path.lineTo(12.4, 6.35)
_path.lineTo(11.86, 5.93)
_path.lineTo(9.7, 5.78)
_path.lineTo(9.7, 4.45)
_path.lineTo(18.3, 4.45)
_path.lineTo(18.3, 5.78)
_path.lineTo(16.14, 5.93)
_path.lineTo(15.6, 6.35)
_path.lineTo(15.6, 21.95)
_path.lineTo(20.22, 21.95)
_path.lineTo(20.64, 21.5)
_path.lineTo(21.06, 17.96)
_path.lineTo(22.71, 17.96)
_path.lineTo(22.71, 23.58)
_path.lineTo(5.29, 23.58)
_path.closeSubpath()


def _isUnicodeChar(text):
        return len(text) and unicodedata.category(text) != "Cc"


class TextTool(BaseTool):
    icon = _path
    name = QApplication.translate("TextTool", "Text")
    shortcut = "T"
    grabKeyboard = True

    def __init__(self, parent=None):
        super().__init__(parent)
        self._caretIndex = 0
        self._engine = None

    @property
    def caretIndex(self):
        return self._caretIndex

    @caretIndex.setter
    def caretIndex(self, index):
        if index != self._caretIndex:
            self._caretIndex = index
            self.parent().setActiveIndex(max(self._caretIndex, 0))
            self.parent().update()

    @property
    def engine(self):
        if self._engine is None and compositor is not None:
            self._engine = LayoutEngine(self._font)
        return self._engine

    def toolActivated(self):
        widget = self.parent()
        self.caretIndex = widget.activeIndex()
        widget.update()

    def toolDisabled(self):
        self._caretIndex = 0
        self.parent().update()

    def drawingAttribute(self, attr, flags):
        if flags.isActiveLayer and attr == "showGlyphFill":
            return True
        return False

    def drawingColor(self, attr, flags):
        if attr == "componentFillColor":
            return Qt.black
        return None

    # helpers

    def _shapeAndSetGlyphs(self, glyphs):
        if self.engine is not None:
            font = self._font
            records = self.engine.process(
                glyph.name for glyph in glyphs)
            # TODO: not sure why we have to do this...
            for glyphRecord in records:
                glyphRecord.glyph = font[glyphRecord.glyphName]
            self.parent().setGlyphRecords(records)
        else:
            self.parent().setGlyphs(glyphs)

    # events

    def keyPressEvent(self, event):
        key = event.key()
        widget = self.parent()
        if key == Qt.Key_Left:
            if self._caretIndex >= 0:
                self.caretIndex -= 1
        elif key == Qt.Key_Right:
            if self._caretIndex < len(list(widget.glyphs())) - 1:
                self.caretIndex += 1
        elif key in (Qt.Key_Backspace, Qt.Key_Delete):
            glyphs = list(widget.glyphs())
            if not glyphs:
                return
            newIndex = self._caretIndex - (key == Qt.Key_Backspace)
            popIndex = newIndex + 1
            if popIndex < 0 or popIndex >= len(glyphs):
                return
            glyphs.pop(popIndex)
            self._shapeAndSetGlyphs(glyphs)
            self.caretIndex = newIndex
        else:
            font = self._font
            name = event.text()
            if not _isUnicodeChar(name):
                return
            glyphName = font.unicodeData.glyphNameForUnicode(ord(name))
            if glyphName in font:
                newCaretIndex = self.caretIndex + 1
                glyphs = list(widget.glyphs())
                glyphs.insert(newCaretIndex, font[glyphName])
                self._shapeAndSetGlyphs(glyphs)
                self.caretIndex = newCaretIndex
                # TODO: also scroll the view to show the cursor

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            widget = self.parent()
            pos = widget.mapFromCanvas(event.localPos())
            index = widget.indexForPoint(pos)
            if index is not None:
                glyph = widget.glyphForIndex(index)
                pos.setX(pos.x() - .5 * (glyph.width * widget.scale()))
                halfIndex = widget.indexForPoint(pos)
                if halfIndex is None:
                    halfIndex = -1 if not index else index
                self.caretIndex = halfIndex
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            widget = self.parent()
            index = widget.indexForPoint(
                widget.mapFromCanvas(event.localPos()))
            if index is not None:
                widget.setActiveIndex(index)
        else:
            super().mouseDoubleClickEvent(event)

    def paint(self, painter, index):
        # XXX: we can't currently draw the caret when there's no
        # glyph on canvas
        widget = self.parent()
        if index != max(self._caretIndex, 0):
            return
        glyphRecord = widget.glyphRecords()[index]
        glyph = glyphRecord.glyph
        xA = glyphRecord.xAdvance
        yA = glyphRecord.yAdvance
        #
        bottom, top = widget.verticalBounds()
        upm = top - bottom
        painter.save()
        pen = painter.pen()
        pen.setColor(QColor(90, 90, 90))
        pen.setWidth(0)
        painter.setPen(pen)
        if self._caretIndex >= 0:
            dx = glyph.width + xA
            dy = glyph.height + yA
        else:
            dx = dy = 0
        painter.translate(dx, bottom + dy)
        painter.drawLine(-30, -25, 0, 0)
        painter.drawLine(0, 0, 30, -25)
        painter.drawLine(0, 0, 0, upm)
        painter.drawLine(-30, upm+25, 0, upm)
        painter.drawLine(0, upm, 30, upm+25)
        painter.restore()
