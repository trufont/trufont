from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QAbstractButton


class PathButton(QAbstractButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drawingCommands = []
        self._isDownColor = None
        self._isFlipped = False
        self._size = QSize(28, 28)

    def drawingCommands(self):
        return self._drawingCommands

    def setDrawingCommands(self, commands):
        self._drawingCommands = commands
        self.update()

    def isFlipped(self):
        return self._isFlipped

    def setIsFlipped(self, value):
        self._isFlipped = value

    def isDownColor(self):
        return self._isDownColor

    def setIsDownColor(self, color):
        self._isDownColor = color
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
        if self._drawingCommands is None:
            return
        painter = QPainter(self)
        rect = event.rect()
        target = self.rect().size()
        size = self._drawingCommands[0]
        if not size.isNull() and (size.width(
                ) < target.width() or size.height() < target.height()):
            dx = dy = 0
            if size.width() < target.width():
                dx = int(.5 * (target.width() - size.width()))
            if size.height() < target.height():
                dy = int(.5 * (target.height() - size.height()))
            painter.translate(dx, dy)
        if self._isDownColor and self.isDown():
            painter.fillRect(rect, self._isDownColor)
        if self._isFlipped:
            painter.translate(0, target.height())
            painter.scale(1, -1)
        for path, cmd, color in self._drawingCommands[1:]:
            if cmd == 'f':
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing)
                painter.fillPath(path, color)
                painter.restore()
            else:
                painter.save()
                if cmd[-1] == 'a':
                    painter.setRenderHint(QPainter.Antialiasing)
                pen = painter.pen()
                pen.setColor(color)
                pen.setWidth(int(cmd[0]))
                painter.setPen(pen)
                painter.drawPath(path)
                painter.restore()

    def minimumSizeHint(self):
        return self.sizeHint()

    def sizeHint(self):
        return self._size
