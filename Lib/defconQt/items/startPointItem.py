from PyQt5.QtCore import QLineF
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsPathItem

startItemDist = 10


class StartPointItem(QGraphicsPathItem):

    def __init__(self, x, y, angle, scale=1, parent=None):
        super(StartPointItem, self).__init__(parent)
        self._angle = 360 - angle

        self.setPointPath(scale)
        self.setPos(x, y)
        self.setZValue(-996)

    def setPointPath(self, scale=None):
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 1.30:
            scale = 1.30
        elif scale < .6:
            scale = .6
        self.prepareGeometryChange()
        dist = startItemDist / scale
        path = QPainterPath()
        line = QLineF(0, 0, 0 + dist, 0)
        line2 = QLineF(line)
        line.setAngle(self._angle - 90)
        path.lineTo(line.x2(), line.y2())
        line2.setAngle(self._angle)
        line2.translate(line.p2() - line.p1())
        path.lineTo(line2.x2(), line2.y2())
        line.setP1(line2.p2())
        line.setAngle(line.angle() - 27.5)
        line.setLength(2 * dist / 5)
        line2.setLength(line2.length() + .5)
        path.moveTo(line.x2(), line.y2())
        path.lineTo(line2.x2(), line2.y2())
        line.setAngle(line.angle() + 55)
        path.lineTo(line.x2(), line.y2())
        self.setPath(path)
