from collections import OrderedDict

from PyQt5.QtCore import QLineF, QPointF, Qt
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QApplication

from trufont.drawingTools.baseTool import BaseTool
from trufont.tools import bezierMath, drawing

_path = QPainterPath()
_path.moveTo(5.11, 23.16)
_path.lineTo(5.72, 24.04)
_path.lineTo(17.2, 12.82)
_path.lineTo(14.28, 9.9)
_path.lineTo(10.89, 10.72)
_path.closeSubpath()
_path.moveTo(15.53, 9.19)
_path.lineTo(18.19, 11.85)
_path.lineTo(22.96, 7.19)
_path.lineTo(19.99, 4.23)
_path.closeSubpath()


class KnifeTool(BaseTool):
    icon = _path
    name = QApplication.translate("KnifeTool", "Knife")
    shortcut = "E"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cachedIntersections = None
        self._knifeLine = None
        self._knifePts = None

    def _appendIntersection(self, contour, index, pt):
        x, y, t = pt
        self._knifePts.append((x, y))
        if (contour, index) in self._cachedIntersections:
            self._cachedIntersections[(contour, index)].append(t)
        else:
            self._cachedIntersections[(contour, index)] = [t]

    def _findIntersections(self):
        self._cachedIntersections = OrderedDict()
        self._knifePts = []
        line = self._knifeLine
        for contour in self._glyph:
            segments = contour.segments
            for index, seg in enumerate(segments):
                if seg[-1].segmentType == "move":
                    continue
                prev = segments[index - 1][-1]
                if len(seg) == 3:
                    if seg[-1].segmentType == "qcurve":
                        i = bezierMath.qcurveIntersections(
                            line.x1(), line.y1(), line.x2(), line.y2(), prev, *seg
                        )
                    else:
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
                        self._appendIntersection(contour, index, pt)
                elif len(seg) == 1:
                    pt = bezierMath.lineIntersection(
                        prev.x,
                        prev.y,
                        seg[0].x,
                        seg[0].y,
                        line.x1(),
                        line.y1(),
                        line.x2(),
                        line.y2(),
                    )
                    if pt is not None:
                        self._appendIntersection(contour, index, pt)

    # events

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.localPos()
            self._knifeLine = QLineF(pos, pos)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            pos = event.localPos()
            if self._knifeLine is None:
                self._knifeLine = QLineF(pos, pos)
                return
            line = self._knifeLine
            if event.modifiers() & Qt.ShiftModifier:
                pos = self.clampToOrigin(pos, line.p1())
            line.setP2(pos)
            self._findIntersections()
            self.parent().update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mouseReleaseEvent(event)
            return
        if self._knifeLine is not None:
            p1, p2 = self._knifeLine.p1(), self._knifeLine.p2()
        self._knifeLine = None
        self._knifePts = None
        self.parent().update()
        # no-move clicks
        if not self._cachedIntersections:
            return
        self._glyph.beginUndoGroup()
        cutContours = (
            not event.modifiers() & Qt.AltModifier
            and len(self._cachedIntersections) > 1
        )
        if cutContours:
            oldPts = {pt for contour in self._glyph for pt in contour}
            path = self._glyph.getRepresentation("defconQt.QPainterPath")
        # reverse so as to not invalidate our cached segment indexes
        for loc, ts in reversed(list(self._cachedIntersections.items())):
            contour, index = loc
            prev = 1
            # reverse so as to cut from higher to lower value and compensate
            for t in sorted(ts, reverse=True):
                contour.splitAndInsertPointAtSegmentAndT(index, t / prev)
                prev = t
        # TODO: optimize
        if cutContours:
            newPts = {
                pt for contour in self._glyph for pt in contour if pt.segmentType
            } - oldPts
            del oldPts

            distances = dict()
            for point in newPts:
                d = bezierMath.distance(p1.x(), p1.y(), point.x, point.y)
                distances[d] = point
            del newPts

            sortedPts = [distances[dist] for dist in sorted(distances.keys())]
            del distances

            # group points by belonging to contour "black area"
            siblings = []
            stack = None
            if not path.contains(p1):
                stack = []
            for pt, nextPt in zip(sortedPts, sortedPts[1:]):
                qPt = QPointF(pt.x, pt.y)
                qHalf = qPt + 0.5 * (QPointF(nextPt.x, nextPt.y) - qPt)
                if path.contains(qHalf):
                    if stack is not None:
                        stack.append(pt)
                else:
                    if stack:
                        stack.append(pt)
                        siblings.extend(stack)
                    stack = []
            if not path.contains(p2):
                if stack:
                    stack.append(nextPt)
                    siblings.extend(stack)
            del stack

            # ok, now i = siblings.index(loc); siblings[i+1-2(i%2)] will yield
            # sibling
            newGlyph = self._glyph.__class__()
            pen = newGlyph.getPointPen()

            def _visitPath(contour, index):
                didJump = False
                pen.beginPath()
                while True:
                    pt = contour.getPoint(index)
                    if pt in visited:
                        pen.endPath()
                        break
                    if pt not in siblings:
                        visited.add(pt)
                    segmentType = pt.segmentType
                    smooth = pt.smooth
                    if didJump or pt in siblings:
                        smooth = False
                        if didJump:
                            segmentType = "line"
                    pen.addPoint((pt.x, pt.y), segmentType, smooth)
                    if pt in siblings and not didJump:
                        i = siblings.index(pt)
                        otherPt = siblings[i + 1 - 2 * (i % 2)]
                        # TODO: optimize-out this lookup
                        for c in self._glyph:
                            try:
                                index = c.index(otherPt)
                            except Exception:
                                pass
                            else:
                                contour = c
                                break
                        didJump = True
                        continue
                    didJump = False
                    index += 1

            visited = set()
            for contour in self._glyph:
                for index, pt in enumerate(contour):
                    if pt in visited or pt in siblings:
                        continue
                    _visitPath(contour, index)
            self._glyph.clearContours()
            pen = self._glyph.getPointPen()
            newGlyph.drawPoints(pen)
        self._glyph.endUndoGroup()
        ##
        self._cachedIntersections = None

    # custom painting

    def paint(self, painter, index):
        widget = self.parent()
        if index != widget.activeIndex():
            return
        line = self._knifeLine
        if line is not None and line.length():
            painter.save()
            pen = painter.pen()
            pen.setWidth(0)
            painter.setPen(pen)
            drawing.drawLine(painter, line.x1(), line.y1(), line.x2(), line.y2())
            if self._knifePts is not None:
                scale = widget.inverseScale()
                dotSize = 5 * scale
                dotHalf = dotSize / 2
                path = QPainterPath()
                for x, y in self._knifePts:
                    x -= dotHalf
                    y -= dotHalf
                    path.addEllipse(x, y, dotSize, dotSize)
                painter.drawPath(path)
            painter.restore()
