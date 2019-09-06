from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QColor, QCursor, QPainter, QPainterPath, QPixmap
from PyQt5.QtWidgets import QApplication, QGraphicsDropShadowEffect

from defconQt.tools.drawing import applyEffectToPixmap

_path = QPainterPath()
_path.moveTo(9, 7.3)
_path.lineTo(9, 24)
_path.lineTo(21, 12)
_path.lineTo(16.3, 12)
_path.lineTo(18.6, 6.6)
_path.lineTo(14.85, 5)
_path.lineTo(12.5, 10.7)
_path.closeSubpath()

path = QPainterPath()
path.moveTo(10, 9.75)
path.lineTo(12.8, 12.5)
path.lineTo(15.3, 6.5)
path.lineTo(17.2, 7.3)
path.lineTo(14.75, 13.1)
path.lineTo(18.5, 13.1)
path.lineTo(10, 21.5)
path.closeSubpath()


class BaseTool(QObject):
    icon = QPainterPath()
    name = QApplication.translate("BaseTool", "Tool")
    shortcut = None
    grabKeyboard = False

    @property
    def cursor(self):
        # TODO: cache?
        return self.makeCursor(_path, path, 9.5, 1)

    def toolActivated(self):
        pass

    def toolDisabled(self):
        pass

    def drawingAttribute(self, attr, flags):
        return None

    def drawingColor(self, attr, flags):
        return None

    @property
    def _font(self):
        return self.parent().window().font_()

    @property
    def _glyph(self):
        return self.parent().activeGlyph()

    # helper functions

    def clampToOrigin(self, pos, origin):
        deltaX = pos.x() - origin.x()
        deltaY = pos.y() - origin.y()
        # go into the first quadrant to simplify our study
        aDeltaX = abs(deltaX)
        aDeltaY = abs(deltaY)
        # diagonal incr.
        # if aDeltaY >= aDeltaX * 2:
        #     pos.setX(origin.x())
        # elif aDeltaY > aDeltaX / 2:
        #     avg = (aDeltaX + aDeltaY) / 2
        #     pos.setX(origin.x() + copysign(avg, deltaX))
        #     pos.setY(origin.y() + copysign(avg, deltaY))
        if aDeltaY >= aDeltaX:
            pos.setX(origin.x())
        else:
            pos.setY(origin.y())
        return pos

    def magnetPos(self, pos):
        widget = self.parent()
        mouseItem = widget.itemAt(pos)
        if isinstance(mouseItem, tuple):
            contour, index = mouseItem
            point = contour[index]
            pos.setX(point.x)
            pos.setY(point.y)
        # TODO: also clamp to (0, 0) and (glyph.width, 0), conditionally?
        return pos

    def makeCursor(self, whitePath, blackPath, x, y):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(0, pixmap.height())
        painter.scale(1, -1)
        painter.fillPath(whitePath, Qt.white)
        painter.end()
        effect = QGraphicsDropShadowEffect()
        effect.setColor(QColor.fromRgbF(0, 0, 0, 0.3))
        effect.setBlurRadius(4)
        effect.setOffset(0, 1)
        pixmap = applyEffectToPixmap(pixmap, effect)
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(0, pixmap.height())
        painter.scale(1, -1)
        painter.fillPath(blackPath, Qt.black)
        painter.end()
        return QCursor(pixmap, x, y)

    # events

    def contextMenuEvent(self, event):
        pass

    def keyPressEvent(self, event):
        pass

    def keyReleaseEvent(self, event):
        pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self._panOrigin = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, "_panOrigin"):
            pos = event.globalPos()
            self.parent().scrollBy(pos - self._panOrigin)
            self._panOrigin = pos

    def mouseReleaseEvent(self, event):
        if hasattr(self, "_panOrigin"):
            del self._panOrigin

    def mouseDoubleClickEvent(self, event):
        pass

    # custom painting

    def paintBackground(self, painter, index):
        pass

    def paint(self, painter, index):
        pass
