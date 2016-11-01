from PyQt5.QtCore import QLineF, Qt
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtWidgets import QApplication
from trufont.drawingTools.baseTool import BaseTool
from trufont.tools import drawing


class RulerTool(BaseTool):
    name = QApplication.translate("RulerTool", "Ruler")
    iconPath = ":ruler.svg"

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
        line = QLineF(x, y, x, y)
        self._rulerObject = (line, "0", "0.0º")

    def mouseMoveEvent(self, event):
        if self._rulerObject is None:
            return
        line, _, _ = self._rulerObject
        canvasPos = event.localPos()
        # magnet before clamping to axis
        canvasPos = self.magnetPos(canvasPos)
        if event.modifiers() & Qt.ShiftModifier:
            canvasPos = self.clampToOrigin(canvasPos, line.p1())
        line.setP2(canvasPos)
        d = str(round(line.length(), 1))
        # angle() doesnt go by trigonometric direction. Weird.
        angle = line.angle()
        angle = 360 * (angle >= 180) - angle
        a = "{}º".format(round(angle, 1))
        self._rulerObject = (line, d, a)
        self.parent().update()

    def mouseReleaseEvent(self, event):
        # double click calls release twice
        if self._rulerObject is None:
            return
        line = self._rulerObject[0]
        if not line.length():
            # delete no-op ruler
            self.toolDisabled()

    # custom painting

    def paint(self, painter):
        widget = self.parent()
        scale = widget.inverseScale()
        # metrics
        if self._rulerObject is not None:
            line, d, a = self._rulerObject
            origin = line.p1()
            cursor = line.p2()
            sz = 8 * scale
            color = QColor(140, 193, 255, 170)

            # line
            painter.save()
            painter.setPen(color)
            drawing.drawLine(
                painter, origin.x(), origin.y(), cursor.x(), cursor.y(), scale)
            path = QPainterPath()
            path.addEllipse(origin.x() - sz / 2, origin.y() - sz / 2, sz, sz)
            path.addEllipse(cursor.x() - sz / 2, cursor.y() - sz / 2, sz, sz)
            painter.fillPath(path, color)
            painter.restore()
            # text
            xAlign = yAlign = "center"
            pos = (origin + cursor) / 2
            drawing.drawTextAtPoint(
                painter, d, pos.x(), pos.y(), scale, xAlign, yAlign)
            xAlign, yAlign = "left", "top"
            dx = cursor.x() - origin.x()
            if dx < 0:
                xAlign = "right"
            drawing.drawTextAtPoint(
                painter, a, cursor.x(), cursor.y(), scale, xAlign, yAlign)
