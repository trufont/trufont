from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QIcon, QIconEngine, QPainter, QPixmap


class PathIconEngine(QIconEngine):
    def __init__(self, width=None, height=None):
        super().__init__()
        self._fillPaths = []
        self._strokePaths = []
        if width is None:
            size = QSize()
        else:
            if height is None:
                height = width
            size = QSize(width, height)
        self._size = size

    def addFillPath(self, path, color=Qt.black, antialiasing=False):
        # TODO: add Mode, State
        self._fillPaths.append((path, color, antialiasing))

    def addStrokePath(self, path, color=Qt.black, width=0.9, antialiasing=False):
        # TODO: add Mode, State
        self._strokePaths.append((path, color, width, antialiasing))

    def size(self):
        return self._size

    def setSize(self, width, height=None):
        if height is None:
            height = width
        self._size = (width, height)

    def paint(self, painter, rect, mode, state):
        # TODO: use Mode, State
        if not (self._fillPaths or self._strokePaths):
            return
        painter.save()
        size = self._size
        target = rect.size()
        if not size.isNull() and (
            size.width() > target.width() or size.height() > target.height()
        ):
            sz = size.scaled(target, Qt.KeepAspectRatio)
            width, height = sz.width() / size.width(), sz.height() / size.height()
            # TODO: don't scale the painter, instead make a rect which
            # coordinates are used to paint in; this will ensure pixel
            # perfection
            painter.scale(width, height)
        for path, color, antialiasing in self._fillPaths:
            painter.setRenderHint(QPainter.Antialiasing, antialiasing)
            painter.fillPath(path, color)
        for path, color, width, antialiasing in self._strokePaths:
            painter.setRenderHint(QPainter.Antialiasing, antialiasing)
            pen = painter.pen()
            pen.setColor(color)
            pen.setWidthF(width)
            painter.setPen(pen)
            painter.drawPath(path)
        painter.restore()

    def pixmap(self, size, mode, state):
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        self.paint(painter, QRect(QPoint(0, 0), size), mode, state)
        painter.end()
        return pixmap


class PathIcon(QIcon):
    def __init__(self, *args):
        self._engine = PathIconEngine(*args)
        super().__init__(self._engine)

    def addFillPath(self, *args, **kwargs):
        self._engine.addFillPath(*args, **kwargs)

    def addStrokePath(self, *args, **kwargs):
        self._engine.addStrokePath(*args, **kwargs)

    def availableSizes(self, mode, state):
        # TODO: use Mode, State
        ret = []
        size = self._engine.size()
        if size.isValid():
            ret.append(size)
        return ret
