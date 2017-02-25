from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QAbstractButton


class PathButton(QAbstractButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(90, 90, 90)
        self._hoverColor = None
        self._fill = self._stroke = False
        self._path = None
        self._pathSize = QSize()
        self._size = QSize(24, 24)

    def color(self):
        return self._color

    def setColor(self, color):
        self._color = color
        self.update()

    def hoverColor(self):
        return self._hoverColor

    def setHoverColor(self, color):
        self._hoverColor = color
        self.update()

    def path(self):
        return self._path

    def setPath(self, path, size=None, fill=True, stroke=False):
        if size is None:
            size = QSize()
        self._path = path
        self._pathSize = size
        self._fill = fill
        self._stroke = stroke
        self.update()

    def size(self):
        return self._size

    def setSize(self, size):
        self._size = size
        self.adjustSize()

    # ----------
    # Qt methods
    # ----------

    def paintEvent(self, event):
        if self._path is None:
            return
        painter = QPainter(self)
        rect = event.rect()
        target = rect.size()
        size = self._pathSize
        if not size.isNull() and (size.width(
                ) > target.width() or size.height() > target.height()):
            sz = size.scaled(target, Qt.KeepAspectRatio)
            width, height = sz.width(
                ) / size.width(), sz.height() / size.height()
            painter.scale(width, height)
        if self._hoverColor and self.isDown():
            painter.fillRect(rect, self._hoverColor)
        painter.translate(0, target.height())
        painter.scale(1, -1)
        if self._fill:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillPath(self._path, self._color)
            painter.restore()
        if self._stroke:
            pen = painter.pen()
            pen.setColor(self._color)
            pen.setWidth(0)
            painter.setPen(pen)
            painter.drawPath(self._path)

    def sizeHint(self):
        return self._size
