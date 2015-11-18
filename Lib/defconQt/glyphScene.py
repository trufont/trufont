import pickle
from math import copysign
from fontTools.misc import bezierTools
from collections import OrderedDict
from defconQt.objects.defcon import TContour, TGlyph

from PyQt5.QtCore import Qt, QMimeData, QLineF, QPointF, QEvent
from PyQt5.QtGui import QKeySequence, QPixmap, QPainterPath
from PyQt5.QtWidgets import (
    QGraphicsItem, QGraphicsSimpleTextItem,
    QGraphicsScene, QApplication)

from defconQt.pens.copySelectionPen import CopySelectionPen
from defconQt.util import platformSpecific
from defconQt.items.anchorItem import AnchorItem
from defconQt.items.componentItem import ComponentItem
from defconQt.items.handleLineItem import HandleLineItem
from defconQt.items.offCurvePointItem import OffCurvePointItem
from defconQt.items.onCurvePointItem import OnCurvePointItem
from defconQt.items.pixmapItem import PixmapItem
from enum import Enum

#TODO: DRY this:
from defconQt.util.roundPosition import roundPosition
offCurvePointSize = 8  # 5
offWidth = offHeight = roundPosition(offCurvePointSize)
# * self._inverseScale)
offHalf = offWidth / 2.0
offCurvePenWidth = 1.0


class SceneTools(Enum):
    SelectionTool = 0
    DrawingTool = 1
    RulerTool = 2
    KnifeTool = 3


class GlyphScene(QGraphicsScene):

    def __init__(self, parent, sceneAddedItems=None):
        super(GlyphScene, self).__init__(parent)
        self._editing = False
        self._integerPlane = True
        self._cachedRuler = None
        self._rulerObject = None
        self._cachedIntersections = None
        self._knifeDots = []
        self._knifeLine = None
        self._dataForUndo = []
        self._dataForRedo = []

        # if this is an array, the Glyphview will clean up all contents
        # when redrawing the active layer
        self._sceneAddedItems = sceneAddedItems

        font = self.font()
        font.setFamily("Roboto Mono")
        font.setFixedPitch(True)
        self.setFont(font)

        self._blocked = False

    def _get_glyphObject(self):
        view = self.views()[0]
        return view._glyph

    _glyphObject = property(
        _get_glyphObject, doc="Get the current glyph in the view.")

    def _addRegisterItem(self, item):
        """The parent object will take care of removing these again"""
        if self._sceneAddedItems is not None:
            self._sceneAddedItems.append(item)
        self.addItem(item)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(GlyphScene, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(GlyphScene, self).dragMoveEvent(event)

    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            paths = mimeData.urls()
            # only support the drop of one image for now
            dragPix = QPixmap(paths[0].toLocalFile())
            event.setAccepted(not dragPix.isNull())
        else:
            return
        pos = event.scenePos()
        pixmapItem = PixmapItem(pos.x(), pos.y(), dragPix, self.getViewScale())
        self._addRegisterItem(pixmapItem)
        event.acceptProposedAction()

    def getItemForPoint(self, point):
        for item in self.items():
            if isinstance(item, OnCurvePointItem) and item._point == point:
                return item
        return None

    def getViewScale(self):
        return self.views()[0].transform().m11()

    # TODO: implement key multiplex in a set()
    # http://stackoverflow.com/a/10568233/2037879
    def keyPressEvent(self, event):
        key = event.key()
        count = event.count()
        modifiers = event.modifiers()
        # XXX: clean this up, prioritize key dispatching before processing
        #      things
        # TODO: this is not DRY w space center, put this in a function
        if modifiers & Qt.ShiftModifier:
            count *= 10
            if modifiers & Qt.ControlModifier:
                count *= 10
        if key == Qt.Key_Left:
            x, y = -count, 0
        elif key == Qt.Key_Up:
            x, y = 0, count
        elif key == Qt.Key_Right:
            x, y = count, 0
        elif key == Qt.Key_Down:
            x, y = 0, -count
        elif key == platformSpecific.deleteKey:
            self._blocked = True
            for item in self.selectedItems():
                if isinstance(item, OnCurvePointItem):
                    item.delete(not event.modifiers() & Qt.ShiftModifier)
                elif isinstance(item, (AnchorItem, ComponentItem,
                                       OffCurvePointItem)):
                    item.delete()
            self._blocked = False
            self._glyphObject.dirty = True
            event.accept()
            return
        elif event.matches(QKeySequence.Undo):
            if len(self._dataForUndo) > 0:
                undo = self._dataForUndo.pop()
                redo = self._glyphObject.serialize()
                self._glyphObject.deserialize(undo)
                self._dataForRedo.append(redo)
            event.accept()
            return
        elif event.matches(QKeySequence.Redo):
            if len(self._dataForRedo) > 0:
                undo = self._glyphObject.serialize()
                redo = self._dataForRedo.pop()
                self._dataForUndo.append(undo)
                self._glyphObject.deserialize(redo)
            event.accept()
            return
        elif event.matches(QKeySequence.SelectAll):
            path = QPainterPath()
            path.addRect(self.sceneRect())
            view = self.views()[0]
            self.setSelectionArea(path, view.transform())
            event.accept()
            return
        elif modifiers & Qt.ControlModifier and key == Qt.Key_D:
            view = self.views()[0]
            self.setSelectionArea(QPainterPath(), view.transform())
            event.accept()
            return
        elif event.matches(QKeySequence.Copy):
            clipboard = QApplication.clipboard()
            mimeData = QMimeData()
            pen = CopySelectionPen()
            self._glyphObject.drawPoints(pen)
            copyGlyph = pen.getGlyph()
            # TODO: somehow try to do this in the pen
            # pass the glyph to a controller object that holds a self._pen
            copyGlyph.width = self._glyphObject.width
            mimeData.setData("application/x-defconQt-glyph-data",
                             pickle.dumps([copyGlyph.serialize(
                                 blacklist=("name", "unicode")
                             )]))
            clipboard.setMimeData(mimeData)
            event.accept()
            return
        elif event.matches(QKeySequence.Paste):
            clipboard = QApplication.clipboard()
            mimeData = clipboard.mimeData()
            if mimeData.hasFormat("application/x-defconQt-glyph-data"):
                data = pickle.loads(mimeData.data(
                    "application/x-defconQt-glyph-data"))
                if len(data) == 1:
                    undo = self._glyphObject.serialize()
                    self._dataForUndo.append(undo)
                    pen = self._glyphObject.getPointPen()
                    pasteGlyph = TGlyph()
                    pasteGlyph.deserialize(data[0])
                    pasteGlyph.drawPoints(pen)
            event.accept()
            return
        else:
            sel = self.selectedItems()
            if (len(sel) == 1 and isinstance(sel[0], OffCurvePointItem) and
                    (sel[0].parentItem().getPointIndex() ==
                        len(sel[0].parentItem()._contour) - 2) and
                    key == Qt.Key_Alt and self._editing is not False):
                sel[0].parentItem().setIsSmooth(False)
            super(GlyphScene, self).keyPressEvent(event)
            return
        if len(self.selectedItems()) == 0:
            super(GlyphScene, self).keyPressEvent(event)
            return
        for item in self.selectedItems():
            # TODO: if isinstance turns out to be slow, we might want to make
            # a selectedMoveBy function in items that calls moveBy for onCurve,
            # noops for offCurve
            if (isinstance(item, OffCurvePointItem) and
                    item.parentItem().isSelected()):
                continue
            item.moveBy(x, y)
        event.accept()

    def keyReleaseEvent(self, event):
        sel = self.selectedItems()
        if (len(sel) == 1 and
                isinstance(sel[0], OffCurvePointItem) and
                sel[0].parentItem().getPointIndex() ==
                len(sel[0].parentItem()._contour) - 2 and
                event.key() == Qt.Key_Alt and
                self._editing is not False):
            sel[0].parentItem().setIsSmooth(True)
        super(GlyphScene, self).keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._rightClickPos = event.scenePos()
        view = self.views()[0]
        touched = self.itemAt(event.scenePos(), view.transform())
        if view._currentTool == SceneTools.RulerTool:
            self.rulerMousePress(event)
            return
        else:
            data = self._glyphObject.serialize()
            self._dataForUndo.append(data)
            self._dataForRedo = []
            if view._currentTool == SceneTools.KnifeTool:
                self.knifeMousePress(event)
                return
            elif view._currentTool == SceneTools.SelectionTool:
                super(GlyphScene, self).mousePressEvent(event)
                return
        self._blocked = True
        forceSelect = False
        sel = self.selectedItems()
        x, y = event.scenePos().x(), event.scenePos().y()
        if self._integerPlane:
            x, y = round(x), round(y)
        # XXX: not sure why isinstance does not work here
        if len(sel) == 1:
            isLastOnCurve = type(sel[0]) is OnCurvePointItem and \
                sel[0]._contour.open and \
                sel[0].getPointIndex() == len(sel[0]._contour) - 1
            # TODO: reimplement convenience methods in OffCurvePointItem
            isLastOffCurve = type(sel[0]) is OffCurvePointItem and \
                sel[0].parentItem()._contour.open and \
                sel[0].parentItem().getPointIndex() + 1 == \
                len(sel[0].parentItem()._contour) - 1
        if len(sel) == 1 and (isLastOffCurve or isLastOnCurve):
            if isLastOnCurve:
                lastContour = sel[0]._contour
            else:
                lastContour = sel[0].parentItem()._contour
            if ((touched and isinstance(touched, OnCurvePointItem)) and
                    touched.getPointIndex() == 0 and
                    lastContour == touched._contour and
                    len(lastContour) > 1):
                # Changing the first point from move to line/curve will cycle
                # and so close the contour
                if isLastOffCurve:
                    lastContour.addPoint((x, y))
                    lastContour[0].segmentType = "curve"
                    touched.childItems()[1].setVisible(True)
                else:
                    lastContour[0].segmentType = "line"
            elif touched and isinstance(touched, OnCurvePointItem):
                super(GlyphScene, self).mousePressEvent(event)
                return
            else:
                if QApplication.keyboardModifiers() & Qt.ShiftModifier:
                    forceSelect = True
                    if isLastOnCurve:
                        refx = sel[0].x()
                        refy = sel[0].y()
                    else:
                        refx = sel[0].parentItem().x()
                        refy = sel[0].parentItem().y()
                    if abs(x - refx) > abs(y - refy):
                        y = copysign(refy, y)
                    else:
                        x = copysign(refx, x)
                if isLastOffCurve:
                    lastContour.addPoint((x, y))
                    lastContour.addPoint((x, y), "curve")
                else:
                    lastContour.addPoint((x, y), "line")
                item = OnCurvePointItem(
                    x, y, False, lastContour, lastContour[-1],
                    self.getViewScale())
                self._addRegisterItem(item)
                for _ in range(2):
                    HandleLineItem(0, 0, 0, 0, item)
                    CPObject = OffCurvePointItem(0, 0, item)
                    CPObject.setVisible(False)
                if isLastOffCurve:
                    item.childItems()[1].setVisible(True)
            lastContour.dirty = True
            self._editing = True
        elif not (touched and isinstance(touched, OnCurvePointItem)):
            nextC = TContour()
            self._glyphObject.appendContour(nextC)
            nextC.addPoint((x, y), "move")

            item = OnCurvePointItem(
                x, y, False,
                self._glyphObject[-1], self._glyphObject[-1][-1],
                self.getViewScale())
            self._addRegisterItem(item)
            for _ in range(2):
                HandleLineItem(0, 0, 0, 0, item)
                CPObject = OffCurvePointItem(0, 0, item)
                CPObject.setVisible(False)
            self._editing = True
        self._blocked = False
        super(GlyphScene, self).mousePressEvent(event)
        # Since shift clamps, we might be missing the point in mousePressEvent
        if forceSelect:
            item.setSelected(True)

    def mouseMoveEvent(self, event):
        if self._editing is True:
            sel = self.selectedItems()
            if (len(sel) == 1 and isinstance(sel[0], OnCurvePointItem) and
                    (event.scenePos() - sel[0].pos()).manhattanLength() >= 2):
                mouseGrabberItem = self.mouseGrabberItem()
                # If we drawn an onCurve w Shift and we're not touching
                # the item, we wont have a mouse grabber (anyways), return
                # early here.
                if mouseGrabberItem is None:
                    event.accept()
                    return
                self._blocked = True
                if len(sel[0]._contour) < 2:
                    # release current onCurve
                    self.sendEvent(sel[0], QEvent(
                        QEvent.MouseButtonRelease))
                    mouseGrabberItem.ungrabMouse()
                    sel[0].setSelected(False)
                    # append an offCurve point and start moving it
                    sel[0]._contour.addPoint(
                        (event.scenePos().x(), event.scenePos().y()))
                    nextCP = sel[0].childItems()[3]
                    nextCP.setVisible(True)
                    nextCP._needsUngrab = True
                    # nextCP.setSelected(True)
                    self.sendEvent(nextCP, QEvent(QEvent.MouseButtonPress))
                    nextCP.grabMouse()
                else:
                    # release current onCurve, delete from contour
                    self.sendEvent(sel[0], QEvent(
                        QEvent.MouseButtonRelease))
                    mouseGrabberItem.ungrabMouse()
                    sel[0].setSelected(False)

                    # construct a curve segment to the current point if
                    # there is not one
                    onCurve = sel[0]._point
                    if not onCurve.segmentType == "curve":
                        # remove the last onCurve
                        sel[0]._contour.removePoint(onCurve)
                        prev = sel[0]._contour[-1]
                        self.getItemForPoint(prev).childItems()[
                            3].setVisible(True)
                        # add a zero-length offCurve to the previous point
                        sel[0]._contour.addPoint((prev.x, prev.y))
                        # add prevOffCurve and activate
                        sel[0]._contour.addPoint((sel[0].x(), sel[0].y()))
                        sel[0].childItems()[1].setVisible(True)
                        # add back current onCurve as a curve point
                        sel[0]._contour.addPoint(
                            (onCurve.x, onCurve.y), "curve")
                        sel[0]._point = sel[0]._contour[-1]
                    if (not QApplication.keyboardModifiers() &
                            Qt.AltModifier):
                        sel[0]._point.smooth = True
                        sel[0]._isSmooth = True
                        sel[0].setPointPath()
                    if sel[0].getPointIndex() == 0:
                        # we're probably dealing with the first point that
                        # we looped.
                        # preserve nextCP whatsoever.
                        lineObj = HandleLineItem(0, 0, 0, 0, sel[0])
                        nextCP = OffCurvePointItem(0, 0, sel[0])
                        # now we have l1, p1, l2, p2, l3, p3
                        l2 = sel[0].childItems()[2]
                        lineObj.stackBefore(l2)
                        nextCP.stackBefore(l2)
                    else:
                        # add last offCurve
                        sel[0]._contour.addPoint((sel[0].x(), sel[0].y()))
                        nextCP = sel[0].childItems()[3]
                    nextCP._needsUngrab = True
                    nextCP.setVisible(True)
                    # nextCP.setSelected(True)
                    self.sendEvent(nextCP, QEvent(QEvent.MouseButtonPress))
                    nextCP.grabMouse()
                self._blocked = False
                self._editing = None
                super(GlyphScene, self).mouseMoveEvent(event)
            elif len(sel) == 1:
                # eat the event
                event.accept()
        else:
            currentTool = self.views()[0]._currentTool
            if currentTool == SceneTools.RulerTool:
                self.rulerMouseMove(event)
                return
            elif currentTool == SceneTools.KnifeTool:
                self.knifeMouseMove(event)
                return
            items = self.items(event.scenePos())
            # XXX: we must cater w mouse tracking
            # we dont need isSelected() once its rid
            if (len(items) > 1 and isinstance(items[0], OnCurvePointItem) and
                    isinstance(items[1], OffCurvePointItem) and
                    items[1].isSelected()):
                items[1].setPos(0, 0)
            else:
                super(GlyphScene, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._editing = False
        currentTool = self.views()[0]._currentTool
        if currentTool == SceneTools.DrawingTool:
            # cleanup extra point elements if we dealt w curved first point
            touched = self.itemAt(event.scenePos(),
                                  self.views()[0].transform())
            if touched and isinstance(touched, OffCurvePointItem):
                onCurve = touched.parentItem()
                children = onCurve.childItems()
                if len(children) > 4:
                    # l1, p1, l3, p3, l2, p2
                    children[3].prepareGeometryChange()
                    self.removeItem(children[3])
                    children[2].prepareGeometryChange()
                    self.removeItem(children[2])

                    onCurve._isSmooth = False
                    onCurve.setPointPath()
                    onCurve._point.smooth = False
        elif currentTool == SceneTools.RulerTool:
            self.rulerMouseRelease(event)
        elif currentTool == SceneTools.KnifeTool:
            self.knifeMouseRelease(event)
        super(GlyphScene, self).mouseReleaseEvent(event)

    def rulerMousePress(self, event):
        touched = self.itemAt(event.scenePos(), self.views()[0].transform())
        if touched is not None and isinstance(touched, OnCurvePointItem) or \
                isinstance(touched, OffCurvePointItem):
            x, y = touched.scenePos().x(), touched.scenePos().y()
        else:
            x, y = event.scenePos().x(), event.scenePos().y()
        if self._integerPlane:
            x, y = round(x), round(y)
        if self._cachedRuler is not None:
            self.removeItem(self._cachedRuler)
            self._cachedRuler = None
        path = QPainterPath()
        path.moveTo(x, y)
        path.lineTo(x + 1, y)
        path.lineTo(x + 1, y + 1)
        path.closeSubpath()
        self._rulerObject = self.addPath(path)
        textItem = QGraphicsSimpleTextItem("0", self._rulerObject)
        font = self.font()
        font.setPointSize(9)
        textItem.setFont(font)
        textItem.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        textItem.setPos(x, y + textItem.boundingRect().height())
        event.accept()

    def rulerMouseMove(self, event):
        # XXX: shouldnt have to do this, it seems mouseTracking is wrongly
        # activated
        if self._rulerObject is None:
            return
        touched = self.itemAt(event.scenePos(), self.views()[0].transform())
        if touched is not None and isinstance(touched, OnCurvePointItem) or \
                isinstance(touched, OffCurvePointItem):
            x, y = touched.scenePos().x(), touched.scenePos().y()
        else:
            # TODO: 45deg clamp w ShiftModifier
            # maybe make a function for that + other occurences...
            x, y = event.scenePos().x(), event.scenePos().y()
        if self._integerPlane:
            x, y = round(x), round(y)
        path = self._rulerObject.path()
        baseElem = path.elementAt(0)
        path.setElementPositionAt(1, x, baseElem.y)
        path.setElementPositionAt(2, x, y)
        path.setElementPositionAt(3, baseElem.x, baseElem.y)
        self._rulerObject.setPath(path)
        textItem = self._rulerObject.childItems()[0]
        line = QLineF(baseElem.x, baseElem.y, x, y)
        l = line.length()
        # XXX: angle() doesnt go by trigonometric direction. Weird.
        # TODO: maybe split in positive/negative 180s (ff)
        a = 360 - line.angle()
        line.setP2(QPointF(x, baseElem.y))
        h = line.length()
        line.setP1(QPointF(x, y))
        v = line.length()
        text = "%d\n↔ %d\n↕ %d\nα %dº" % (l, h, v, a)
        textItem.setText(text)
        dx = x - baseElem.x
        if dx >= 0:
            px = x
        else:
            px = x - textItem.boundingRect().width()
        dy = y - baseElem.y
        if dy > 0:
            py = baseElem.y
        else:
            py = baseElem.y + textItem.boundingRect().height()
        textItem.setPos(px, py)
        event.accept()

    def rulerMouseRelease(self, event):
        textItem = self._rulerObject.childItems()[0]
        if textItem.text() == "0":
            # delete no-op ruler
            self.removeItem(self._rulerObject)
            self._rulerObject = None
        else:
            self._cachedRuler = self._rulerObject
            self._rulerObject = None
        event.accept()

    def knifeMousePress(self, event):
        scenePos = event.scenePos()
        x, y = scenePos.x(), scenePos.y()
        self._knifeLine = self.addLine(x, y, x, y)
        event.accept()

    """
    Computes intersection between a cubic spline and a line segment.
    Adapted from: https://www.particleincell.com/2013/cubic-line-intersection/

    Takes four defcon points describing curve and four scalars describing line
    parameters.
    """

    def computeIntersections(self, p1, p2, p3, p4, x1, y1, x2, y2):
        bx, by = x1 - x2, y2 - y1
        m = x1 * (y1 - y2) + y1 * (x2 - x1)
        a, b, c, d = bezierTools.calcCubicParameters(
            (p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y), (p4.x, p4.y))

        pc0 = by * a[0] + bx * a[1]
        pc1 = by * b[0] + bx * b[1]
        pc2 = by * c[0] + bx * c[1]
        pc3 = by * d[0] + bx * d[1] + m
        r = bezierTools.solveCubic(pc0, pc1, pc2, pc3)

        sol = []
        for t in r:
            s0 = a[0] * t ** 3 + b[0] * t ** 2 + c[0] * t + d[0]
            s1 = a[1] * t ** 3 + b[1] * t ** 2 + c[1] * t + d[1]
            if (x2 - x1) != 0:
                s = (s0 - x1) / (x2 - x1)
            else:
                s = (s1 - y1) / (y2 - y1)
            if not (t < 0 or t > 1 or s < 0 or s > 1):
                sol.append((s0, s1, t))
        return sol

    """
    G. Bach, http://stackoverflow.com/a/1968345
    """

    def lineIntersection(self, x1, y1, x2, y2, x3, y3, x4, y4):
        Bx_Ax = x2 - x1
        By_Ay = y2 - y1
        Dx_Cx = x4 - x3
        Dy_Cy = y4 - y3
        determinant = (-Dx_Cx * By_Ay + Bx_Ax * Dy_Cy)
        if abs(determinant) < 1e-20:
            return []
        s = (-By_Ay * (x1 - x3) + Bx_Ax * (y1 - y3)) / determinant
        t = (Dx_Cx * (y1 - y3) - Dy_Cy * (x1 - x3)) / determinant
        if s >= 0 and s <= 1 and t >= 0 and t <= 1:
            return [(x1 + (t * Bx_Ax), y1 + (t * By_Ay), t)]
        return []

    def knifeMouseMove(self, event):
        # XXX: shouldnt have to do this, it seems mouseTracking is wrongly
        # activated
        if self._knifeLine is None:
            return
        for dot in self._knifeDots:
            self.removeItem(dot)
        self._knifeDots = []
        scenePos = event.scenePos()
        x, y = scenePos.x(), scenePos.y()
        line = self._knifeLine.line()
        line.setP2(QPointF(x, y))
        # XXX: not nice
        glyph = self.views()[0]._glyph
        self._cachedIntersections = OrderedDict()
        for contour in glyph:
            segments = contour.segments
            for index, seg in enumerate(segments):
                if seg[-1].segmentType == "move":
                    continue
                prev = segments[index - 1][-1]
                if len(seg) == 3:
                    i = self.computeIntersections(
                        prev, seg[0], seg[1], seg[2],
                        line.x1(), line.y1(), x, y)
                else:
                    i = self.lineIntersection(
                        prev.x, prev.y, seg[0].x, seg[0].y,
                        line.x1(), line.y1(), x, y)
                for pt in i:
                    scale = self.getViewScale()
                    item = self.addEllipse(-offHalf / scale, -offHalf / scale,
                                           offWidth / scale, offHeight / scale)
                    item.setPos(pt[0], pt[1])
                    if (contour, index) in self._cachedIntersections:
                        self._cachedIntersections[(contour, index)].append(
                            pt[2])
                    else:
                        self._cachedIntersections[(contour, index)] = [pt[2]]
                    self._knifeDots.append(item)
        self._knifeLine.setLine(line)
        event.accept()

    def knifeMouseRelease(self, event):
        self.removeItem(self._knifeLine)
        self._knifeLine = None
        for dot in self._knifeDots:
            self.removeItem(dot)
        self._knifeDots = []
        # no-move clicks
        if self._cachedIntersections is None:
            return
        # reverse so as to not invalidate our cached segment indexes
        for loc, ts in reversed(list(self._cachedIntersections.items())):
            contour, index = loc
            prev = 1
            # reverse so as to cut from higher to lower value and compensate
            for t in sorted(ts, reverse=True):
                contour.splitAndInsertPointAtSegmentAndT(index, t / prev)
                prev = t
        self._cachedIntersections = None
        event.accept()
