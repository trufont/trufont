import unicodedata

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QKeySequence, QPainterPath
from PyQt5.QtWidgets import QApplication

from trufont.drawingTools.baseTool import BaseTool

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


# XXX: rewind the shaped string when metrics change/anchors are moved


class TextTool(BaseTool):
    icon = _path
    name = QApplication.translate("TextTool", "Text")
    shortcut = "T"
    grabKeyboard = True

    def __init__(self, parent=None):
        super().__init__(parent)

    @property
    def _layoutManager(self):
        return self.parent().layoutManager()

    # TODO: we might want to fold this into LayoutManager
    def _insertUnicodings(self, text):
        unicodeData = self._font.unicodeData
        for c in text:
            glyphName = unicodeData.glyphNameForUnicode(ord(c))
            if glyphName is not None:
                self._layoutManager.insert(glyphName)

    # methods

    def toolActivated(self):
        widget = self.parent()
        # XXX: don't disable tool on setGlyphs, then uncomment this
        # self._layoutManager.initCaret()
        widget.update()

    def toolDisabled(self):
        self.parent().update()

    def drawingAttribute(self, attr, flags):
        if flags.isActiveLayer:
            return attr in ("showGlyphFill", "showGlyphComponentFill")
        return False

    def drawingColor(self, attr, flags):
        if attr == "componentFillColor":
            return Qt.black
        return None

    # events

    def keyPressEvent(self, event):
        key = event.key()
        if event.matches(QKeySequence.Paste):
            # XXX: the menu item should also go down this codepath
            clipboard = QApplication.clipboard()
            mimeData = clipboard.mimeData()
            if mimeData.hasText():
                self._insertUnicodings(mimeData.text())
        elif key == Qt.Key_Left:
            # TODO: we'll probably need to reform this stuff for RTL
            self._layoutManager.caretPrevious()
        elif key == Qt.Key_Right:
            self._layoutManager.caretNext()
        elif key in (Qt.Key_Backspace, Qt.Key_Delete):
            self._layoutManager.delete(forward=(key == Qt.Key_Delete))
        else:
            text = event.text()
            if not _isUnicodeChar(text):
                return
            # text should be just one codepoint, but be safe
            self._insertUnicodings(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.parent().mapFromCanvas(event.localPos())
            self._layoutManager.setCaretFromPos(pos)
        else:
            super().mousePressEvent(event)

    def paintBackground(self, painter, index):
        # XXX: we can't currently draw the caret when there's no
        # glyph on canvas
        offset = self._layoutManager.drawingOffset(index)
        if offset is None:
            return
        dx, dy = offset
        bottom, top = self.parent().verticalBounds()
        upm = top - bottom

        painter.save()
        pen = painter.pen()
        pen.setColor(QColor(90, 90, 90))
        pen.setWidth(0)
        painter.setPen(pen)
        painter.translate(dx, bottom + dy)
        painter.drawLine(-30, -25, 0, 0)
        painter.drawLine(0, 0, 30, -25)
        painter.drawLine(0, 0, 0, upm)
        painter.drawLine(-30, upm + 25, 0, upm)
        painter.drawLine(0, upm, 30, upm + 25)
        painter.restore()
