import itertools
from collections import OrderedDict

from PyQt5.QtCore import QLineF, QPointF, Qt
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtWidgets import QApplication

from trufont.drawingTools.baseTool import BaseTool
from trufont.tools import bezierMath, drawing

_path = QPainterPath()
_path.moveTo(4.1, 19.94)
_path.lineTo(19.94, 4.1)
_path.lineTo(23.9, 8.06)
_path.lineTo(22.25, 9.71)
_path.lineTo(20.92, 8.4)
_path.lineTo(19.94, 9.38)
_path.lineTo(21.26, 10.7)
_path.lineTo(19.94, 12.02)
_path.lineTo(17.63, 9.71)
_path.lineTo(16.64, 10.7)
_path.lineTo(18.95, 13.01)
_path.lineTo(17.63, 14.33)
_path.lineTo(16.31, 13.01)
_path.lineTo(15.32, 14)
_path.lineTo(16.64, 15.32)
_path.lineTo(15.32, 16.64)
_path.lineTo(13.01, 14.33)
_path.lineTo(12.02, 15.32)
_path.lineTo(14.33, 17.63)
_path.lineTo(13.01, 18.95)
_path.lineTo(11.69, 17.63)
_path.lineTo(10.7, 18.62)
_path.lineTo(12.02, 19.94)
_path.lineTo(10.7, 21.26)
_path.lineTo(8.4, 18.95)
_path.lineTo(7.4, 19.94)
_path.lineTo(9.71, 22.25)
_path.lineTo(8.06, 23.9)
_path.closeSubpath()


class RulerTool(BaseTool):
    icon = _path
    name = QApplication.translate("RulerTool", "Ruler")
    shortcut = "L"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cachedIntersections = None
        self._rulerObject = None
        self._rulerPts = None

    def toolActivated(self):
        self.parent().update()

    def toolDisabled(self):
        self._cachedIntersections = None
        self._rulerObject = None
        self._rulerPts = None
        self.parent().update()

    def drawingAttribute(self, attr, flags):
        if flags.isActiveLayer and attr == "showGlyphPointCoordinates":
            return True
        return super().drawingAttribute(attr, flags)

    # custom methods

    def _appendIntersection(self, pt):
        x, y, _ = pt
        line = QLineF(self._rulerObject[0])
        line.setP2(QPointF(x, y))
        self._rulerPts[line.length()] = (x, y)

    def _findIntersections(self):
        self._cachedIntersections = OrderedDict()
        self._rulerPts = dict()
        line = self._rulerObject[0]

        # the default layer stores the width
        defaultGlyph = self._glyph.layerSet.defaultLayer.get(self._glyph.name)
        if defaultGlyph is not None:
            width = defaultGlyph.width
            info = defaultGlyph.font.info
            ascender = info.ascender or 750
            descender = info.descender or -250
            for x in (0, width):
                pt = bezierMath.lineIntersection(
                    line.x1(),
                    line.y1(),
                    line.x2(),
                    line.y2(),
                    x,
                    descender,
                    x,
                    ascender,
                )
                if pt is not None:
                    self._appendIntersection(pt)

        for contour in self._glyph:
            segments = contour.segments
            for index, seg in enumerate(segments):
                if seg[-1].segmentType == "move":
                    continue
                prev = segments[index - 1][-1]
                if seg[-1].segmentType == "curve":
                    i = bezierMath.curveIntersections(
                        line.x1(),
                        line.y1(),
                        line.x2(),
                        line.y2(),
                        prev,
                        seg[0],
                        seg[1],
                        seg[2],
                    )
                    for pt in i:
                        self._appendIntersection(pt)
                elif len(seg) == 1:
                    pt = bezierMath.lineIntersection(
                        line.x1(),
                        line.y1(),
                        line.x2(),
                        line.y2(),
                        prev.x,
                        prev.y,
                        seg[0].x,
                        seg[0].y,
                    )
                    if pt is not None:
                        self._appendIntersection(pt)

    # events

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.magnetPos(event.localPos())
            line = QLineF(pos, pos)
            self._rulerObject = (line, "0.0º")
            self._rulerPts = dict()
            self.parent().update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            pos = self.magnetPos(event.localPos())
            if self._rulerObject is None:
                self._rulerObject = (QLineF(pos, pos), "0.0º")
                return
            line, _ = self._rulerObject
            # magnet done before clamping to axis
            if event.modifiers() & Qt.ShiftModifier:
                pos = self.clampToOrigin(pos, line.p1())
            line.setP2(pos)
            # angle() doesnt go by trigonometric direction. Weird.
            angle = line.angle()
            angle = 360 * (angle >= 180) - angle
            a = "{}º".format(round(angle, 1))
            self._rulerObject = (line, a)
            self._rulerPts = dict()
            if not event.modifiers() & Qt.AltModifier:
                self._findIntersections()
            self.parent().update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # double click calls release twice
            if self._rulerObject is None:
                return
            line = self._rulerObject[0]
            if not line.length():
                # delete no-op ruler
                self.toolDisabled()
        else:
            super().mouseReleaseEvent(event)

    # custom painting

    def paint(self, painter, index):
        widget = self.parent()
        if index != widget.activeIndex():
            return
        scale = widget.inverseScale()
        # metrics
        if self._rulerObject is not None:
            line, a = self._rulerObject
            origin = line.p1()
            cursor = line.p2()
            size = 8 * scale
            halfSize = 4 * scale
            color = QColor(255, 85, 127, 170)

            # line
            painter.save()
            painter.setPen(color)
            drawing.drawLine(
                painter, origin.x(), origin.y(), cursor.x(), cursor.y(), scale
            )
            # ellipses
            ellipses = [(origin.x(), origin.y()), (cursor.x(), cursor.y())]
            path = QPainterPath()
            path.setFillRule(Qt.WindingFill)
            for x, y in itertools.chain(self._rulerPts.values(), ellipses):
                x -= halfSize
                y -= halfSize
                path.addEllipse(x, y, size, size)
            painter.fillPath(path, color)
            painter.restore()
            # text
            line = QLineF(line)
            xAlign = yAlign = "center"
            ellipses.pop(0)
            rp = self._rulerPts
            # XXX: sort shouldn't be performed in paintEvent
            for pt in itertools.chain((rp[k] for k in sorted(rp)), ellipses):
                p = QPointF(*pt)
                line.setP2(p)
                if line.length():
                    d = str(round(line.length(), 1))
                    pos = (line.p1() + line.p2()) / 2
                    drawing.drawTextAtPoint(
                        painter, d, pos.x(), pos.y(), scale, xAlign, yAlign
                    )
                line.setP1(p)
            xAlign, yAlign = "left", "top"
            dx = cursor.x() - origin.x()
            px = size
            if dx < 0:
                xAlign = "right"
                px = -px
            drawing.drawTextAtPoint(
                painter, a, cursor.x() + px, cursor.y() + size, scale, xAlign, yAlign
            )
