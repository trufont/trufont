from collections import OrderedDict
from PyQt5.QtCore import QLineF, Qt
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QApplication
from trufont.drawingTools.baseTool import BaseTool
from trufont.tools import bezierMath, drawing


class KnifeTool(BaseTool):
    name = QApplication.translate("KnifeTool", "Knife")
    iconPath = ":cutter.svg"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cachedIntersections = None
        self._knifeLine = None
        self._knifeDots = None

    def _appendIntersection(self, contour, index, pt, dotHalf, dotWidth):
        dotHeight = dotWidth
        x = pt[0] - dotHalf
        y = pt[1] - dotHalf
        self._knifeDots.addEllipse(x, y, dotWidth, dotHeight)
        if (contour, index) in self._cachedIntersections:
            self._cachedIntersections[(contour, index)].append(
                pt[2])
        else:
            self._cachedIntersections[(contour, index)] = [pt[2]]

    # events

    def mousePressEvent(self, event):
        canvasPos = event.localPos()
        self._knifeLine = QLineF(canvasPos, canvasPos)

    def mouseMoveEvent(self, event):
        if self._knifeLine is None:
            return
        line = self._knifeLine
        pos = event.localPos()
        widget = self.parent()
        if event.modifiers() & Qt.ShiftModifier:
            pos = self.clampToOrigin(pos, line.p1())
        line.setP2(pos)
        self._cachedIntersections = OrderedDict()
        scale = widget.inverseScale()
        dotWidth = 5 * scale
        dotHalf = dotWidth / 2.0
        self._knifeDots = QPainterPath()
        for contour in self._glyph:
            segments = contour.segments
            for index, seg in enumerate(segments):
                if seg[-1].segmentType == "move":
                    continue
                prev = segments[index - 1][-1]
                if len(seg) == 3:
                    i = bezierMath.curveIntersections(
                        prev, seg[0], seg[1], seg[2],
                        line.x1(), line.y1(), pos.x(), pos.y())
                    for pt in i:
                        self._appendIntersection(
                            contour, index, pt, dotHalf, dotWidth)
                else:
                    pt = bezierMath.lineIntersection(
                        prev.x, prev.y, seg[0].x, seg[0].y,
                        line.x1(), line.y1(), pos.x(), pos.y())
                    if pt is not None:
                        self._appendIntersection(
                            contour, index, pt, dotHalf, dotWidth)
        widget.update()

    def mouseReleaseEvent(self, event):
        self._knifeLine = None
        self._knifeDots = None
        # no-move clicks
        if self._cachedIntersections is None:
            return
        self._glyph.prepareUndo()
        # reverse so as to not invalidate our cached segment indexes
        for loc, ts in reversed(list(self._cachedIntersections.items())):
            contour, index = loc
            prev = 1
            # reverse so as to cut from higher to lower value and compensate
            for t in sorted(ts, reverse=True):
                contour.splitAndInsertPointAtSegmentAndT(index, t / prev)
                prev = t
        self._cachedIntersections = None
        self.parent().update()

    # custom painting

    def paint(self, painter):
        line = self._knifeLine
        if line is not None and line.length():
            painter.save()
            pen = painter.pen()
            pen.setWidth(0)
            painter.setPen(pen)
            drawing.drawLine(
                painter, line.x1(), line.y1(), line.x2(), line.y2())
            if self._knifeDots is not None:
                painter.drawPath(self._knifeDots)
            painter.restore()
