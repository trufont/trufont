from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QMenu, QRubberBand, QStyle, QStyleOptionRubberBand, QApplication)
from defcon import Component
from trufont.controls.glyphDialogs import AddAnchorDialog, AddComponentDialog
from trufont.drawingTools.baseTool import BaseTool
from trufont.objects.defcon import TAnchor
from trufont.tools import bezierMath, platformSpecific
from trufont.tools.uiMethods import (
    deleteUISelection, maybeProjectUISmoothPointOffcurve, moveUISelection,
    removeUISelection)
from trufont.windows.glyphWindow import GlyphWindow

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
            anchor = self._glyph.instantiateAnchor()
            anchor.x = pos.x()
            anchor.y = pos.y()
            anchor.name = newAnchorName
            self._glyph.appendAnchor(anchor)

    def _createComponent(self, *args):
        widget = self.parent()
        newGlyph, ok = AddComponentDialog.getNewGlyph(widget, self._glyph)
        if ok and newGlyph is not None:
            component = self._glyph.instantiateComponent()
            component.baseGlyph = newGlyph.name
            self._glyph.appendComponent(component)

    def _goToGlyph(self, glyphName):
        widget = self.parent()
        font = self._glyph.getParent()
        if glyphName in font:
            glyph = font[glyphName]
            glyphWindow = GlyphWindow(glyph, widget.parent())
            glyphWindow.show()

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

    def _findSegmentUnderMouse(self, pos, action=None):
        scale = self.parent().inverseScale()
        for contour in self._glyph:
            for index, point in enumerate(contour):
                if point.segmentType == "line":
                    prev = contour.getPoint(index-1)
                    dist = bezierMath.lineDistance(
                        prev.x, prev.y, point.x, point.y, pos.x(), pos.y())
                    # TODO: somewhat arbitrary
                    if dist < 5 * scale:
                        return [prev, point], contour
                elif point.segmentType == "curve":
                    if action == "insert":
                        continue
                    bez = [contour.getPoint(index-3+i) for i in range(4)]
                    if _pointWithinThreshold(pos.x(), pos.y(), bez, 5 * scale):
                        return bez, contour
        return None

    def _performSegmentClick(self, pos, action=None, segmentTuple=None):
        if segmentTuple is None:
            segmentTuple = self._findSegmentUnderMouse(pos, action)
        if segmentTuple is None:
            return
        segment, contour = segmentTuple
        prev, point = segment[0], segment[-1]
        if point.segmentType == "line":
            if action == "insert":
                index = contour.index(point)
                self._glyph.prepareUndo()
                contour.holdNotifications()
                for i, t in enumerate((.35, .65)):
                    xt = prev.x + t * (point.x - prev.x)
                    yt = prev.y + t * (point.y - prev.y)
                    contour.insertPoint(
                        index+i, point.__class__((xt, yt)))
                point.segmentType = "curve"
                contour.releaseHeldNotifications()
                return
        elif point.segmentType != "curve":
            return
        if action == "selectContour":
            contour.selected = not contour.selected
            self._shouldMove = self._shouldPrepareUndo = True

    def _maybeJoinContour(self, pos):
        def getAtEdge(contour, pt):
            for index in range(2):
                if contour[index-1] == pt:
                    return index - 1
            return None

        if self._itemTuple is None:
            return
        item, parent = self._itemTuple
        if parent is None or not (item.segmentType and parent.open):
            return
        ptIndex = getAtEdge(parent, item)
        if ptIndex is None:
            return
        widget = self.parent()
        items = widget.itemsAt(pos)
        for point, contour in zip(items["points"], items["contours"]):
            if point == item or not (point.segmentType and contour.open):
                continue
            otherIndex = getAtEdge(contour, point)
            if otherIndex is None:
                continue
            if parent != contour:
                # TODO: blacklist single onCurve contours
                # Note reverse uses different point objects
                # TODO: does it have to work this way?
                if not ptIndex:
                    parent.reverse()
                if otherIndex == -1:
                    contour.reverse()
                dragPoint = parent[-1]
                parent.removePoint(dragPoint)
                contour[0].segmentType = dragPoint.segmentType
                contour.drawPoints(parent)
                glyph = contour.glyph
                glyph.removeContour(contour)
                parent.dirty = True
            else:
                if item.segmentType == "move":
                    item.x = point.x
                    item.y = point.y
                    contour.removePoint(point)
                else:
                    contour.removePoint(item)
                contour[0].segmentType = "line"
                contour.dirty = True
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
            elif isinstance(item, Component):
                menu.addSeparator()
                menu.addAction(self.tr("Go To Glyph"),
                               lambda: self._goToGlyph(item.baseGlyph))
                menu.addAction(self.tr("Decompose Component"),
                               lambda: self._glyph.decomposeComponent(item))
                menu.addAction(self.tr("Decompose All"),
                               self._glyph.decomposeAllComponents)
        menu.exec_(self._cachedPos)
        self._cachedPos = None

    # events

    def keyPressEvent(self, event):
        key = event.key()
        if platformSpecific.isDeleteEvent(event):
            glyph = self._glyph
            # TODO: fuse more the two methods, they're similar and delete is
            # Cut except not putting in the clipboard
            if event.modifiers() & Qt.AltModifier:
                deleteUISelection(glyph)
            else:
                preserveShape = not event.modifiers() & Qt.ShiftModifier
                # TODO: prune
                glyph.prepareUndo()
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
        self._origin = self._prevPos = pos = self.magnetPos(event.localPos())
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
            action = "insert" if event.modifiers() & Qt.AltModifier else None
            segmentTuple = self._findSegmentUnderMouse(pos, action)
            if segmentTuple is not None:
                segment, contour = segmentTuple
                selected = segment[0].selected and segment[-1].selected
            else:
                selected = False
            if not selected:
                if addToSelection:
                    self._oldSelection = self._glyph.selection
                else:
                    for anchor in self._glyph.anchors:
                        anchor.selected = False
                    for component in self._glyph.components:
                        component.selected = False
                    self._glyph.selected = False
                    self._glyph.image.selected = False
                self._performSegmentClick(pos, action, segmentTuple)
            else:
                self._shouldMove = True
        widget.update()

    def mouseMoveEvent(self, event):
        canvasPos = event.localPos()
        glyph = self._glyph
        widget = self.parent()
        if self._shouldMove or self._itemTuple is not None:
            if self._shouldPrepareUndo:
                self._glyph.prepareUndo()
                self._shouldPrepareUndo = False
            modifiers = event.modifiers()
            if self._itemTuple is not None:
                # Alt: move point along handles
                if modifiers & Qt.AltModifier and len(glyph.selection) == 1:
                    item, parent = self._itemTuple
                    if parent is not None:
                        x, y = canvasPos.x(), canvasPos.y()
                        didMove = self._moveOnCurveAlongHandles(
                            parent, item, x, y)
                        if didMove:
                            return
                # Shift: clamp pos on axis
                elif modifiers & Qt.ShiftModifier:
                        item, parent = self._itemTuple
                        if parent is not None:
                            if item.segmentType is None:
                                onCurve = self._getOffCurveSiblingPoint(
                                    parent, item)
                                canvasPos = self.clampToOrigin(
                                    canvasPos, QPointF(onCurve.x, onCurve.y))
                            else:
                                canvasPos = self.clampToOrigin(
                                    canvasPos, self._origin)
            dx = canvasPos.x() - self._prevPos.x()
            dy = canvasPos.y() - self._prevPos.y()
            for anchor in glyph.anchors:
                if anchor.selected:
                    anchor.move((dx, dy))
            for contour in glyph:
                moveUISelection(contour, (dx, dy))
            for component in glyph.components:
                if component.selected:
                    component.move((dx, dy))
            image = glyph.image
            if image.selected:
                image.move((dx, dy))
            self._prevPos = canvasPos
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
                glyph.selection = points
        widget.update()

    def mouseReleaseEvent(self, event):
        self._maybeJoinContour(event.localPos())
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
                    # if we have one offCurve, make it tangent
                    maybeProjectUISmoothPointOffcurve(contour, point)
        else:
            self._performSegmentClick(event.localPos(), "selectContour")

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
        painter.resetTransform()
        widget.style().drawControl(
            QStyle.CE_RubberBand, option, painter, widget)
        painter.restore()
