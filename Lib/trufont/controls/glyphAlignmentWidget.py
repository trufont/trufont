from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath
from PyQt5.QtWidgets import QSizePolicy, QWidget


class GlyphAlignmentWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self._alignment = None
        self._alignmentPaths = []
        self._glyph = None

        self._circleRadius = 4
        self._padding = 1

    def alignment(self):
        return self._alignment

    def setAlignment(self, value):
        self._alignment = value

    def glyph(self):
        return self._glyph

    def setGlyph(self, glyph):
        self._glyph = glyph

    def origin(self):
        alignment = self._alignment
        glyph = self._glyph
        if None in (alignment, glyph, glyph.controlPointBounds):
            return (0, 0)
        left, bottom, right, top = glyph.controlPointBounds
        if not alignment % 3:
            x = left
        elif not (alignment - 2) % 3:
            x = right
        else:
            x = (left + right) / 2
        if alignment < 3:
            y = top
        elif alignment > 5:
            y = bottom
        else:
            y = (top + bottom) / 2
        return (x, y)

    def circleRadius(self):
        return self._circleRadius

    def setCircleRadius(self, value):
        self._circleRadius = value

    def padding(self):
        return self._padding

    def setPadding(self, value):
        self._padding = value

    # ----------
    # Qt methods
    # ----------

    def sizeHint(self):
        return QSize(42, 42)

    def mousePressEvent(self, event):
        if event.button() & Qt.LeftButton:
            pos = event.localPos()
            for index, path in enumerate(self._alignmentPaths):
                if path.contains(pos):
                    if self._alignment == index:
                        self._alignment = None
                    else:
                        self._alignment = index
                    self.update()
                    break
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        self._alignmentPaths = []
        painter = QPainter(self)
        painter.setPen(QColor(45, 45, 45))

        circleRadius = self._circleRadius
        padding = self._padding
        rect = event.rect()
        size = min(rect.height(), rect.width())
        offset = .5 * (rect.width() - size)
        painter.translate(offset, 0)
        borderRect = rect.__class__(
            rect.left() + circleRadius + padding,
            rect.top() + circleRadius + padding,
            size - 2 * (circleRadius + padding),
            size - 2 * (circleRadius + padding))
        borderPath = QPainterPath()
        borderPath.addRect(*borderRect.getRect())

        columnCount = 3
        radioPath = QPainterPath()
        selectedPath = QPainterPath()
        for row in range(columnCount):
            for col in range(columnCount):
                index = row * columnCount + col
                path = QPainterPath()
                path.addEllipse(
                    padding + col * .5 * borderRect.width(),
                    padding + row * .5 * borderRect.height(),
                    2 * circleRadius, 2 * circleRadius)
                if self._alignment == index:
                    selectedPath = path
                self._alignmentPaths.append(path.translated(offset, 0))
                radioPath.addPath(path)
        painter.drawPath(borderPath - radioPath)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPath(radioPath)
        painter.fillPath(selectedPath, Qt.black)
