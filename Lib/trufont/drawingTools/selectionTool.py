from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QKeySequence, QPainter, QPainterPath, QTransform
from PyQt5.QtWidgets import (
    QMenu, QRubberBand, QStyle, QStyleOptionRubberBand, QApplication)
from trufont.controls.glyphDialogs import AddAnchorDialog, AddComponentDialog
from trufont.drawingTools.baseTool import BaseTool
from trufont.objects.defcon import TAnchor, TComponent
from trufont.tools import bezierMath
from trufont.tools.uiMethods import moveUISelection, removeUISelection

arrowKeys = (Qt.Key_Left, Qt.Key_Up, Qt.Key_Right, Qt.Key_Down)
navKeys = (Qt.Key_Less, Qt.Key_Greater)


def _pointWithinThreshold(x, y, curve, eps):
    """
    See whether *(x, y)* is within *eps* of *curve*.
    """
    path = QPainterPath()
    path.addEllipse(x - eps, y - eps, 2 * eps, 2 * eps)
    curvePath = QPainterPath()
    p1, p2, p3, p4 = curve
    curvePath.moveTo(p1.x, p1.y)
    curvePath.cubicTo(p2.x, p2.y, p3.x, p3.y, p4.x, p4.y)
    curvePath.cubicTo(p3.x, p3.y, p2.x, p2.y, p1.x, p1.y)
    return path.intersects(curvePath)


class SelectionTool(BaseTool):
    name = QApplication.translate("SelectionTool", "Selection")
    iconPath = ":cursor.svg"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._itemTuple = None
        self._oldSelection = set()
        self._rubberBandRect = None
        self._shouldMove = False
        self._shouldPrepareUndo = False

    # helpers

    def _createAnchor(self, *args):
        widget = self.parent()
        pos = widget.mapToCanvas(widget.mapFromGlobal(self._cachedPos))
        newAnchorName, ok = AddAnchorDialog.getNewAnchorName(widget, pos)
        if ok:
            anchor = TAnchor()
            anchor.x = pos.x()
            anchor.y = pos.y()
            anchor.name = newAnchorName
            self._glyph.appendAnchor(anchor)

    def _createComponent(self, *args):
        widget = self.parent()
        newGlyph, ok = AddComponentDialog.getNewGlyph(widget, self._glyph)
        if ok and newGlyph is not None:
            component = TComponent()
            component.baseGlyph = newGlyph.name
            self._glyph.appendComponent(component)

    def _getSelectedCandidatePoint(self):
        """
        If there is exactly one point selected in the glyph, return it.

        Else return None.
        """

        candidates = set()
        for contour in self._glyph:
            sel = contour.selection
            if len(sel) > 1:
                return None
            elif not len(sel):
                continue
            pt = next(iter(sel))
            candidates.add((pt, contour))
        if len(candidates) == 1:
            return next(iter(candidates))
        return None

    def _getOffCurveSiblingPoint(self, contour, point):
        index = contour.index(point)
        for d in (-1, 1):
            sibling = contour.getPoint(index + d)
            if sibling.segmentType is not None:
                return sibling
        raise IndexError

    def _moveOnCurveAlongHandles(self, contour, pt, x, y):
        # TODO: offCurves
        if pt.segmentType is not None and pt.smooth and len(contour) >= 3:
            index = contour.index(pt)
            prevCP = contour.getPoint(index - 1)
            nextCP = contour.getPoint(index + 1)
            # we need at least one offCurve so that it makes sense
            # slide the onCurve around
            if prevCP.segmentType is None or nextCP.segmentType is None:
                projX, projY, _ = bezierMath.lineProjection(
                    prevCP.x, prevCP.y, nextCP.x, nextCP.y, x, y, False)
                # short-circuit UIMove because we're only moving this point
                pt.x = projX
                pt.y = projY
                contour.dirty = True
                return True
        return False

    def _computeSegmentClick(self, pos, insert=False):
        scale = self.parent().inverseScale()
        for contour in self._glyph:
            for index, point in enumerate(contour):
                if point.segmentType == "line":
                    prev = contour.getPoint(index-1)
                    dist = bezierMath.lineDistance(
                        prev.x, prev.y, point.x, point.y, pos.x(), pos.y())
                    # TODO: somewhat arbitrary
                    if dist < 5 * scale:
                        if insert:
                            self._glyph.prepareUndo()
                            contour.holdNotifications()
                            for i, t in enumerate((.35, .65)):
                                xt = prev.x + t * (point.x - prev.x)
                                yt = prev.y + t * (point.y - prev.y)
                                contour.insertPoint(
                                    index+i, point.__class__((xt, yt)))
                            point.segmentType = "curve"
                            contour.releaseHeldNotifications()
                        else:
                            prev.selected = point.selected = True
                            contour.postNotification(
                                notification="Contour.SelectionChanged")
                            self._shouldMove = self._shouldPrepareUndo = True
                        return
                elif point.segmentType == "curve":
                    if insert:
                        continue
                    bez = [contour.getPoint(index-3+i) for i in range(4)]
                    if _pointWithinThreshold(pos.x(), pos.y(), bez, 5 * scale):
                        prev = bez[0]
                        prev.selected = point.selected = True
                        contour.postNotification(
                            notification="Contour.SelectionChanged")
                        self._shouldMove = self._shouldPrepareUndo = True
                        return

    def _moveForEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        dx, dy = 0, 0
        if key == Qt.Key_Left:
            dx = -1
        elif key == Qt.Key_Up:
            dy = 1
        elif key == Qt.Key_Right:
            dx = 1
        elif key == Qt.Key_Down:
            dy = -1
        if modifiers & Qt.ShiftModifier:
            dx *= 10
            dy *= 10
            if modifiers & Qt.ControlModifier:
                dx *= 10
                dy *= 10
        return (dx, dy)

    def _renameAnchor(self, anchor):
        widget = self.parent()
        newAnchorName, ok = AddAnchorDialog.getNewAnchorName(
            widget, None, anchor.name)
        if ok:
            anchor.name = newAnchorName

    def _reverse(self):
        selectedContours = set()
        for contour in self._glyph:
            if contour.selection:
                selectedContours.add(contour)
        target = selectedContours or self._glyph
        for contour in target:
            contour.reverse()

    def _setStartPoint(self, point, contour):
        index = contour.index(point)
        contour.setStartPoint(index)

    # actions

    def showContextMenu(self, event):
        widget = self.parent()
        self._cachedPos = event.globalPos()
        menu = QMenu(widget)
        menu.addAction(self.tr("Add Anchor…"), self._createAnchor)
        menu.addAction(self.tr("Add Component…"), self._createComponent)
        menu.addAction(self.tr("Reverse"), self._reverse)
        itemTuple = widget.itemAt(event.localPos())
        if itemTuple is not None:
            item, parent = itemTuple
            if parent is not None and item.segmentType:
                menu.addSeparator()
                menu.addAction(self.tr("Set Start Point"),
                               lambda: self._setStartPoint(item, parent))
        menu.exec_(self._cachedPos)
        self._cachedPos = None

    # events

    def keyPressEvent(self, event):
        key = event.key()
        if event.matches(QKeySequence.Delete):
            glyph = self._glyph
            # TODO: prune
            glyph.prepareUndo()
            preserveShape = not event.modifiers() & Qt.ShiftModifier
            for anchor in glyph.anchors:
                if anchor.selected:
                    glyph.removeAnchor(anchor)
            for contour in reversed(glyph):
                removeUISelection(contour, preserveShape)
            for component in glyph.components:
                if component.selected:
                    glyph.removeComponent(component)
            if glyph.image.selected:
                glyph.image = None
        elif key in arrowKeys:
            # TODO: prune
            self._glyph.prepareUndo()
            delta = self._moveForEvent(event)
            # TODO: seems weird that glyph.selection and selected don't incl.
            # anchors and components while glyph.move does... see what glyphs
            # does
            hadSelection = False
            for anchor in self._glyph.anchors:
                if anchor.selected:
                    anchor.move(delta)
                    hadSelection = True
            for contour in self._glyph:
                moveUISelection(contour, delta)
                # XXX: shouldn't have to recalc this
                if contour.selection:
                    hadSelection = True
            for component in self._glyph.components:
                if component.selected:
                    component.move(delta)
                    hadSelection = True
            image = self._glyph.image
            if image.selected:
                image.move(delta)
                hadSelection = True
            if not hadSelection:
                event.ignore()
        elif key in navKeys:
            pack = self._getSelectedCandidatePoint()
            if pack is not None:
                point, contour = pack
                point.selected = False
                index = contour.index(point)
                offset = int(key == Qt.Key_Greater) or -1
                newPoint = contour.getPoint(index + offset)
                newPoint.selected = True
                contour.postNotification(
                    notification="Contour.SelectionChanged")

    def mousePressEvent(self, event):
        if event.button() & Qt.RightButton:
            self.showContextMenu(event)
            return
        widget = self.parent()
        addToSelection = event.modifiers() & Qt.ControlModifier
        self._origin = self.magnetPos(event.localPos())
        self._itemTuple = widget.itemAt(self._origin)
        if self._itemTuple is not None:
            itemUnderMouse, parentContour = self._itemTuple
            if not (itemUnderMouse.selected or addToSelection):
                for anchor in self._glyph.anchors:
                    anchor.selected = False
                for component in self._glyph.components:
                    component.selected = False
                self._glyph.selected = False
                self._glyph.image.selected = False
            itemUnderMouse.selected = True
            if parentContour is not None:
                parentContour.postNotification(
                    notification="Contour.SelectionChanged")
            self._shouldPrepareUndo = True
        else:
            if addToSelection:
                self._oldSelection = self._glyph.selection
            else:
                for anchor in self._glyph.anchors:
                    anchor.selected = False
                for component in self._glyph.components:
                    component.selected = False
                self._glyph.selected = False
                self._glyph.image.selected = False
            self._computeSegmentClick(event.localPos())
        widget.update()

    def mouseMoveEvent(self, event):
        canvasPos = event.localPos()
        widget = self.parent()
        if self._shouldMove or self._itemTuple is not None:
            if self._shouldPrepareUndo:
                self._glyph.prepareUndo()
                self._shouldPrepareUndo = False
            modifiers = event.modifiers()
            # Alt: move point along handles
            if modifiers & Qt.AltModifier and len(self._glyph.selection) == 1:
                item, parent = self._itemTuple
                if parent is not None:
                    x, y = canvasPos.x(), canvasPos.y()
                    didMove = self._moveOnCurveAlongHandles(parent, item, x, y)
                    if didMove:
                        return
            # Shift: clamp pos on axis
            elif modifiers & Qt.ShiftModifier:
                item, parent = self._itemTuple
                if parent is not None:
                    if item.segmentType is None:
                        onCurve = self._getOffCurveSiblingPoint(parent, item)
                        canvasPos = self.clampToOrigin(
                            canvasPos, QPointF(onCurve.x, onCurve.y))
            dx = canvasPos.x() - self._origin.x()
            dy = canvasPos.y() - self._origin.y()
            for anchor in self._glyph.anchors:
                if anchor.selected:
                    anchor.move((dx, dy))
            for contour in self._glyph:
                moveUISelection(contour, (dx, dy))
            for component in self._glyph.components:
                if component.selected:
                    component.move((dx, dy))
            image = self._glyph.image
            if image.selected:
                image.move((dx, dy))
            self._origin = canvasPos
        else:
            self._rubberBandRect = QRectF(self._origin, canvasPos).normalized()
            items = widget.items(self._rubberBandRect)
            points = set(items["points"])
            if event.modifiers() & Qt.ControlModifier:
                points ^= self._oldSelection
            # TODO: fine-tune this more, maybe add optional args to items...
            if event.modifiers() & Qt.AltModifier:
                points = set(pt for pt in points if pt.segmentType)
            if points != self._glyph.selection:
                # TODO: doing this takes more time than by-contour
                # discrimination for large point count
                self._glyph.selection = points
        widget.update()

    def mouseReleaseEvent(self, event):
        self._itemTuple = None
        self._oldSelection = set()
        self._rubberBandRect = None
        self._shouldMove = False
        self.parent().update()

    def mouseDoubleClickEvent(self, event):
        widget = self.parent()
        self._itemTuple = widget.itemAt(self._origin)
        if self._itemTuple is not None:
            item, parent = self._itemTuple
            if parent is None:
                if isinstance(item, TAnchor):
                    self._renameAnchor(item)
            else:
                point, contour = item, parent
                if point.segmentType is not None:
                    self._glyph.prepareUndo()
                    point.smooth = not point.smooth
                contour.dirty = True
        else:
            self._computeSegmentClick(event.localPos(), True)

    # custom painting

    def paint(self, painter):
        if self._rubberBandRect is None:
            return
        widget = self.parent()
        # okay, OS-native rubber band does not support painting with
        # floating-point coordinates
        # paint directly on the widget with unscaled context
        widgetOrigin = widget.mapFromCanvas(self._rubberBandRect.bottomLeft())
        widgetMove = widget.mapFromCanvas(self._rubberBandRect.topRight())
        option = QStyleOptionRubberBand()
        option.initFrom(widget)
        option.opaque = False
        option.rect = QRectF(widgetOrigin, widgetMove).toRect()
        option.shape = QRubberBand.Rectangle
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setTransform(QTransform())
        widget.style().drawControl(
            QStyle.CE_RubberBand, option, painter, widget)
        painter.restore()
