from trufont.tools.baseTool import BaseTool
from trufont.util import drawing
from PyQt5.QtCore import QLineF, QPointF, Qt
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QApplication


class RulerTool(BaseTool):
    name = QApplication.translate("RulerTool", "Ruler")
    iconPath = ":/resources/ruler.svg"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rulerObject = None

    def toolDisabled(self):
        self._rulerObject = None
        self.parent().update()

    # events

    def mousePressEvent(self, event):
        pos = self.magnetPos(event.localPos())
        x, y = pos.x(), pos.y()
        path = QPainterPath()
        path.moveTo(x, y)
        path.lineTo(x + 1, y)
        path.lineTo(x + 1, y + 1)
        path.closeSubpath()
        text = "0"
        self._rulerObject = (path, text)

    def mouseMoveEvent(self, event):
        path, text = self._rulerObject
        baseElem = path.elementAt(0)
        canvasPos = event.localPos()
        if event.modifiers() & Qt.ShiftModifier:
            basePos = QPointF(baseElem.x, baseElem.y)
            canvasPos = self.clampToOrigin(canvasPos, basePos)
        canvasPos = self.magnetPos(canvasPos)
        x, y = canvasPos.x(), canvasPos.y()
        path.setElementPositionAt(1, x, baseElem.y)
        path.setElementPositionAt(2, x, y)
        path.setElementPositionAt(3, baseElem.x, baseElem.y)
        line = QLineF(baseElem.x, baseElem.y, x, y)
        l = line.length()
        # angle() doesnt go by trigonometric direction. Weird.
        # TODO: maybe split in positive/negative 180s (ff)
        a = 360 - line.angle()
        line.setP2(QPointF(x, baseElem.y))
        h = line.length()
        line.setP1(QPointF(x, y))
        v = line.length()
        text = "%d\n↔ %d\n↕ %d\nα %dº" % (l, h, v, a)
        self._rulerObject = (path, text)
        self.parent().update()

    def mouseReleaseEvent(self, event):
        text = self._rulerObject[1]
        if text == "0":
            # delete no-op ruler
            self.toolDisabled()

    # custom painting

    def paint(self, painter):
        if self._rulerObject is not None:
            path, text = self._rulerObject
            painter.drawPath(path)
            baseElem = path.elementAt(0)
            cursorElem = path.elementAt(2)
            # work out text alignment
            # to do that we need to find out which quadrant the ruler is
            # operating in
            xAlign, yAlign = "left", "bottom"
            dx = cursorElem.x - baseElem.x
            if dx < 0:
                xAlign = "right"
            dy = cursorElem.y - baseElem.y
            if dy <= 0:
                yAlign = "top"
            # XXX: draw multiLines arg
            drawing.drawTextAtPoint(
                painter, text, cursorElem.x, baseElem.y,
                self.parent()._inverseScale, xAlign, yAlign)
