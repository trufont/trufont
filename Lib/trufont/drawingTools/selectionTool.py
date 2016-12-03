from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPalette, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QMenu, QRubberBand, QStyle, QStyleOptionRubberBand, QApplication)
from defcon import Anchor, Component, Glyph, Guideline
from fontTools.pens.basePen import decomposeQuadraticSegment
from trufont.controls.glyphDialogs import AddComponentDialog, RenameDialog
from trufont.drawingTools.baseTool import BaseTool
from trufont.tools import bezierMath, platformSpecific
from trufont.tools.uiMethods import (
    deleteUISelection, maybeProjectUISmoothPointOffcurve, moveUIGlyphElements,
    removeUIGlyphElements, unselectUIGlyphElements)
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
    if curve[-1].segmentType == "curve":
        p1, p2, p3, p4 = curve
        curvePath.moveTo(p1.x, p1.y)
        curvePath.cubicTo(p2.x, p2.y, p3.x, p3.y, p4.x, p4.y)
        curvePath.cubicTo(p3.x, p3.y, p2.x, p2.y, p1.x, p1.y)
    else:
        first = curve[0]
        curvePath.moveTo(first.x, first.y)
        # PACK for fontTools
        pts = []
        for pt in curve:
            pts.append((pt.x, pt.y))
        # draw
        for pt1, pt2 in decomposeQuadraticSegment(pts[1:]):
            curvePath.quadTo(*pt1+pt2)
        for pt1, pt2 in decomposeQuadraticSegment(list(reversed(pts[:-1]))):
            curvePath.quadTo(*pt1+pt2)
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
        glyph = self._glyph
        glyph.prepareUndo()
        pos = widget.mapToCanvas(widget.mapFromGlobal(self._cachedPos))
        # remove template anchors
        for anchor in glyph.anchors:
            if anchor.name == "new anchor":
                glyph.removeAnchor(anchor)
        # add one at position
        anchor = glyph.instantiateAnchor()
        anchor.x = pos.x()
        anchor.y = pos.y()
        anchor.name = "new anchor"
        glyph.appendAnchor(anchor)

    def _createComponent(self, *args):
        widget = self.parent()
        glyph = self._glyph
        glyph.prepareUndo()
        newGlyph, ok = AddComponentDialog.getNewGlyph(widget, glyph)
        if ok and newGlyph is not None:
            component = glyph.instantiateComponent()
            component.baseGlyph = newGlyph.name
            glyph.appendComponent(component)

    def _createGuideline(self, *args):
        widget = self.parent()
        glyph = self._glyph
        glyph.prepareUndo()
        pos = widget.mapToCanvas(widget.mapFromGlobal(self._cachedPos))
        content = dict(x=pos.x(), y=pos.y())
        guideline = glyph.instantiateGuideline(content)
        glyph.appendGuideline(guideline)

    def _goToGlyph(self, glyphName):
        widget = self.parent()
        font = self._glyph.font
        if glyphName in font:
            glyph = font[glyphName]
            glyphWindow = GlyphWindow(glyph, widget.window().parent())
            glyphWindow.show()

    def _toggleGuideline(self, guideline):
        glyph = self._glyph
        font = glyph.font
        if font is None:
            return
        if isinstance(guideline.getParent(), Glyph):
            glyph.removeGuideline(guideline)
            font.appendGuideline(guideline)
        else:
            font.removeGuideline(guideline)
            glyph.appendGuideline(guideline)

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
        ret = False
        if pt.segmentType is not None:
            if pt.smooth and len(contour) >= 3:
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
                    ret = True
            else:
                # non-smooth onCurve we just move, not moving any other point
                pt.x = x
                pt.y = y
                ret = True
        else:
            index = contour.index(pt)
            onCurve = None
            for delta in (-1, 1):
                pt_ = contour.getPoint(index + delta)
                if pt_.segmentType is not None:
                    onCurve = pt_
            if onCurve is not None:
                # keep new pt tangent to onCurve -> pt segment,
                # i.e. do an orthogonal projection
                pt.x, pt.y, _ = bezierMath.lineProjection(
                    onCurve.x, onCurve.y, pt.x, pt.y, x, y, False)
                ret = True
        if ret:
            contour.dirty = True
        return ret

    def _findSegmentUnderMouse(self, pos, action=None):
        scale = self.parent().inverseScale()
        for contour in self._glyph:
            for index, point in enumerate(contour):
                if point.segmentType == "line":
                    prev = contour.getPoint(index-1)
                    dist = bezierMath.lineDistance(
                        prev.x, prev.y, point.x, point.y, pos.x(), pos.y())
                    # TODO: somewhat arbitrary
                    if dist <= 3 * scale:
                        return [prev, point], contour
                elif point.segmentType in ("curve", "qcurve"):
                    if action == "insert":
                        continue
                    if point.segmentType == "curve":
                        bez = [contour.getPoint(index-3+i) for i in range(4)]
                    else:
                        bez = [point]
                        i = 1
                        while i < 2 or point.segmentType is None:
                            point = contour.getPoint(index-i)
                            bez.append(point)
                            i += 1
                        bez.reverse()
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
        elif point.segmentType not in ("curve", "qcurve"):
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

    def _renameItem(self, item):
        widget = self.parent()
        newName, ok = RenameDialog.getNewName(widget, item.name)
        if ok:
            item.name = newName

    def _reverse(self, target=None):
        if target is None:
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
        itemTuple = widget.itemAt(event.localPos())
        targetContour = None
        if itemTuple is not None:
            item, parent = itemTuple
            if parent is not None and item.segmentType:
                targetContour = [parent]
                menu.addAction(self.tr("Set Start Point"),
                               lambda: self._setStartPoint(item, parent))
            elif isinstance(item, Component):
                menu.addAction(self.tr("Go To Glyph"),
                               lambda: self._goToGlyph(item.baseGlyph))
                menu.addAction(self.tr("Decompose"),
                               lambda: self._glyph.decomposeComponent(item))
                menu.addAction(self.tr("Decompose All"),
                               self._glyph.decomposeAllComponents)
            elif isinstance(item, Guideline):
                if isinstance(item.getParent(), Glyph):
                    text = self.tr("Make Global")
                else:
                    text = self.tr("Make Local")
                menu.addAction(text, lambda: self._toggleGuideline(item))
        if targetContour is not None:
            reverseText = self.tr("Reverse Contour")
        else:
            # XXX: text and action shouldnt be decoupled
            if self._glyph.selection:
                reverseText = self.tr("Reverse Selected Contours")
            else:
                reverseText = self.tr("Reverse All Contours")
        menu.addAction(reverseText, lambda: self._reverse(targetContour))
        menu.addSeparator()
        menu.addAction(self.tr("Add Component…"), self._createComponent)
        menu.addAction(self.tr("Add Anchor"), self._createAnchor)
        menu.addAction(self.tr("Add Guideline"), self._createGuideline)
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
                removeUIGlyphElements(glyph, preserveShape)
        elif key in arrowKeys:
            # TODO: prune
            self._glyph.prepareUndo()
            dx, dy = self._moveForEvent(event)
            # TODO: seems weird that glyph.selection and selected don't incl.
            # anchors and components while glyph.move does... see what glyphs
            # does
            moveUIGlyphElements(self._glyph, dx, dy)
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
        elif key == Qt.Key_Return:
            changed = False
            for contour in self._glyph:
                for index, point in enumerate(contour):
                    if point.segmentType is not None:
                        if all(contour.getPoint(
                                index + d).segmentType for d in (-1, 1)):
                            continue
                        if not changed:
                            self._glyph.prepareUndo()
                            changed = True
                        point.smooth = not point.smooth
                    contour.dirty = True

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
                unselectUIGlyphElements(self._glyph)
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
                    unselectUIGlyphElements(self._glyph)
                self._performSegmentClick(pos, action, segmentTuple)
            else:
                self._shouldMove = self._shouldPrepareUndo = True
        widget.update()

    def mouseMoveEvent(self, event):
        glyph = self._glyph
        widget = self.parent()
        if self._shouldMove or self._itemTuple is not None:
            canvasPos = event.pos()
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
            moveUIGlyphElements(glyph, dx, dy)
            self._prevPos = canvasPos
        else:
            canvasPos = event.localPos()
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
                if isinstance(item, (Anchor, Guideline)):
                    self._renameItem(item)
            else:
                point, contour = item, parent
                if point.segmentType is not None:
                    index = contour.index(point)
                    if all(contour.getPoint(index + d).segmentType for d in (
                            -1, 1)):
                        return
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
        rect = self._rubberBandRect
        # TODO: maybe extract this to drawRubberBand
        if platformSpecific.needsCustomRubberBand():
            highlight = widget.palette(
                ).color(QPalette.Active, QPalette.Highlight)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.setPen(highlight.darker(120))
            highlight.setAlphaF(.35)
            painter.setBrush(highlight)
            painter.drawRect(rect)
            painter.restore()
        else:
            # okay, OS-native rubber band does not support painting with
            # floating-point coordinates
            # paint directly on the widget with unscaled context
            widgetOrigin = widget.mapFromCanvas(rect.bottomLeft())
            widgetMove = widget.mapFromCanvas(rect.topRight())
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
