from defcon import Anchor, Component, Glyph, Guideline
from fontTools.pens.basePen import decomposeQuadraticSegment
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPalette
from PyQt5.QtWidgets import (
    QApplication,
    QMenu,
    QRubberBand,
    QStyle,
    QStyleOptionRubberBand,
)

from trufont.controls.glyphDialogs import AddComponentDialog, EditDialog
from trufont.drawingTools.baseTool import BaseTool
from trufont.tools import bezierMath, platformSpecific
from trufont.tools.uiMethods import (
    maybeProjectUISmoothPointOffcurve,
    moveUIGlyphElements,
    unselectUIGlyphElements,
)

arrowKeys = (Qt.Key_Left, Qt.Key_Up, Qt.Key_Right, Qt.Key_Down)
navKeys = (Qt.Key_Less, Qt.Key_Greater)

_path = QPainterPath()
_path.moveTo(15.33, 4.18)
_path.lineTo(12.36, 11.2)
_path.lineTo(8.37, 7.46)
_path.lineTo(8.37, 23.87)
_path.lineTo(20.85, 12.05)
_path.lineTo(15.33, 12.05)
_path.lineTo(18.17, 5.36)
_path.closeSubpath()


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
            curvePath.quadTo(*pt1 + pt2)
        for pt1, pt2 in decomposeQuadraticSegment(list(reversed(pts[:-1]))):
            curvePath.quadTo(*pt1 + pt2)
    return path.intersects(curvePath)


class SelectionTool(BaseTool):
    icon = _path
    name = QApplication.translate("SelectionTool", "Select")
    shortcut = "V"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._origin = None
        self._mouseItem = None
        self._oldPath = None
        self._oldSelection = set()
        self._rubberBandRect = None
        self._shouldMove = False

    # helpers

    def _createAnchor(self, *_):
        widget = self.parent()
        glyph = self._glyph
        pos = widget.mapToCanvas(widget.mapFromGlobal(self._cachedPos))
        # remove template anchors
        for anchor in glyph.anchors:
            if anchor.name == "new anchor":
                glyph.removeAnchor(anchor)
        # add one at position
        anchor = dict(x=pos.x(), y=pos.y(), name="new anchor")
        glyph.appendAnchor(anchor)
        self._editItem(glyph.anchors[-1])

    def _createComponent(self, *_):
        widget = self.parent()
        glyph = self._glyph
        newGlyph, ok = AddComponentDialog.getNewGlyph(widget, glyph)
        if ok and newGlyph is not None:
            component = glyph.instantiateComponent()
            component.baseGlyph = newGlyph.name
            glyph.appendComponent(component)

    def _createGuideline(self, *_):
        widget = self.parent()
        glyph = self._glyph
        pos = widget.mapToCanvas(widget.mapFromGlobal(self._cachedPos))
        guideline = dict(x=pos.x(), y=pos.y(), angle=0)
        glyph.appendGuideline(guideline)

    def _goToGlyph(self, glyphName):
        widget = self.parent()
        font = self._glyph.font
        if glyphName in font:
            glyph = font[glyphName]
            fontWindow = widget.window()
            fontWindow.openGlyphTab(glyph)

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

    def _findSegmentUnderMouse(self, pos, action=None):
        scale = self.parent().inverseScale()
        for contour in self._glyph:
            for index, point in enumerate(contour):
                if point.segmentType == "line":
                    prev = contour.getPoint(index - 1)
                    dist = bezierMath.lineDistance(
                        prev.x, prev.y, point.x, point.y, pos.x(), pos.y()
                    )
                    # TODO: somewhat arbitrary
                    if dist <= 3 * scale:
                        return [prev, point], contour
                elif point.segmentType in ("curve", "qcurve"):
                    if action == "insert":
                        continue
                    if point.segmentType == "curve":
                        bez = [contour.getPoint(index - 3 + i) for i in range(4)]
                    else:
                        bez = [point]
                        i = 1
                        while i < 2 or point.segmentType is None:
                            point = contour.getPoint(index - i)
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
            return False
        segment, contour = segmentTuple
        prev, point = segment[0], segment[-1]
        if point.segmentType == "line":
            if action == "insert":
                index = contour.index(point) or len(contour)
                contour.holdNotifications()
                for i, t in enumerate((0.35, 0.65)):
                    xt = prev.x + t * (point.x - prev.x)
                    yt = prev.y + t * (point.y - prev.y)
                    contour.insertPoint(index + i, point.__class__((xt, yt)))
                point.segmentType = "curve"
                contour.releaseHeldNotifications()
                return True
        elif point.segmentType not in ("curve", "qcurve"):
            return True
        if action == "selectContour":
            contour.selected = not contour.selected
            self._shouldMove = True
        return True

    def _maybeJoinContour(self, pos):
        if self._mouseItem is None or not isinstance(self._mouseItem, tuple):
            return
        contour, index = self._mouseItem
        point = contour[index]
        if not (point.segmentType and contour.open):
            return
        if index not in (0, len(contour) - 1):
            return
        widget = self.parent()
        items = widget.itemsAt(pos)
        for c, i in items["points"]:
            p = c[i]
            if p == point or not (p.segmentType and c.open):
                continue
            if i not in (0, len(c) - 1):
                continue
            if c != contour:
                # TODO: blacklist single onCurve contours
                # Note reverse uses different point objects
                # TODO: does it have to work this way?
                # update: I think frederik changed that in master defcon
                if not index:
                    contour.reverse()
                if i == -1:
                    c.reverse()
                dragPoint = contour[-1]
                contour.removePoint(dragPoint)
                c[0].segmentType = dragPoint.segmentType
                c.drawPoints(contour)
                glyph = c.glyph
                glyph.removeContour(c)
                contour.dirty = True
            else:
                if point.segmentType == "move":
                    point.x = p.x
                    point.y = p.y
                    c.removePoint(p)
                else:
                    c.removePoint(point)
                c[0].segmentType = "line"
                c.dirty = True
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

    def _editItem(self, item):
        widget = self.parent()
        newName, x, y, ok = EditDialog.getNewProperties(widget, item)
        if ok:
            item.name = newName
            item.x = x
            item.y = y

    def _reverse(self, target=None):
        if target is None:
            selectedContours = set()
            for contour in self._glyph:
                if contour.selection:
                    selectedContours.add(contour)
            target = selectedContours or self._glyph
        if not target:
            return
        self._glyph.holdNotifications()
        for contour in target:
            contour.reverse()
        self._glyph.releaseHeldNotifications()

    def _setStartPoint(self, contour, index):
        if not index:
            return
        contour.setStartPoint(index)

    # events

    def contextMenuEvent(self, event):
        widget = self.parent()
        self._cachedPos = event.globalPos()
        menu = QMenu(widget)
        item = widget.itemAt(event.localPos())
        targetContour = None
        if item is not None:
            if isinstance(item, tuple):
                contour, index = item
                targetContour = contour
                if True or contour[index].segmentType is not None:  # XXX
                    menu.addAction(
                        self.tr("Set Start Point"),
                        lambda: self._setStartPoint(contour, index),
                    )
            elif isinstance(item, Component):
                menu.addAction(
                    self.tr("Go To Glyph"), lambda: self._goToGlyph(item.baseGlyph)
                )
                menu.addAction(
                    self.tr("Decompose"), lambda: self._glyph.decomposeComponent(item)
                )
                menu.addAction(
                    self.tr("Decompose All"), self._glyph.decomposeAllComponents
                )
            elif isinstance(item, Guideline):
                if isinstance(item.getParent(), Glyph):
                    text = self.tr("Make Global")
                else:
                    text = self.tr("Make Local")
                menu.addAction(text, lambda: self._toggleGuideline(item))
        if len(self._glyph):
            if targetContour is not None:
                reverseText = self.tr("Reverse Contour")
                target = [targetContour]
            else:
                # XXX: text and action shouldnt be decoupled
                if self._glyph.selection:
                    reverseText = self.tr("Reverse Selected Contours")
                else:
                    reverseText = self.tr("Reverse All Contours")
                target = None
            menu.addAction(reverseText, lambda: self._reverse(target))
            menu.addSeparator()
        if len(self._glyph.layer) > 1:
            menu.addAction(self.tr("Add Component…"), self._createComponent)
        menu.addAction(self.tr("Add Anchor"), self._createAnchor)
        menu.addAction(self.tr("Add Guideline"), self._createGuideline)
        menu.exec_(self._cachedPos)
        self._cachedPos = None

    def keyPressEvent(self, event):
        key = event.key()
        # XXX: this shouldn't be tool-specific!
        if key in arrowKeys:
            dx, dy = self._moveForEvent(event)
            modifiers = event.modifiers()
            kwargs = dict()
            if modifiers == platformSpecific.combinedModifiers():
                kwargs["nudgePoints"] = True
            elif modifiers & Qt.AltModifier:
                kwargs["slidePoints"] = True
            moveUIGlyphElements(self._glyph, dx, dy, **kwargs)
        # TODO: nav shouldn't be specific to this tool
        elif key in navKeys:
            pack = self._getSelectedCandidatePoint()
            if pack is not None:
                point, contour = pack
                point.selected = False
                index = contour.index(point)
                offset = int(key == Qt.Key_Greater) or -1
                newPoint = contour.getPoint(index + offset)
                newPoint.selected = True
                contour.postNotification(notification="Contour.SelectionChanged")
        elif key == Qt.Key_Return:
            self._glyph.beginUndoGroup()
            for contour in self._glyph:
                for index, point in enumerate(contour):
                    changed = False
                    if point.segmentType is not None and point.selected:
                        if all(
                            contour.getPoint(index + d).segmentType for d in (-1, 1)
                        ):
                            continue
                        point.smooth = not point.smooth
                        changed = True
                    if changed:
                        contour.dirty = True
            self._glyph.endUndoGroup()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        widget = self.parent()
        addToSelection = event.modifiers() & Qt.ControlModifier
        self._glyph.beginUndoGroup()
        self._origin = self._prevPos = pos = self.magnetPos(event.localPos())
        self._mouseItem = widget.itemAt(self._origin)
        if self._mouseItem is not None:
            item = self._mouseItem
            contour = None
            if isinstance(item, tuple):
                contour, i = item
                item = contour[i]
            if not (item.selected or addToSelection):
                unselectUIGlyphElements(self._glyph)
            if addToSelection:
                item.selected = not item.selected
            else:
                item.selected = True
            if contour is not None:
                contour.postNotification(notification="Contour.SelectionChanged")
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
                self._shouldMove = True
        if self._mouseItem is not None or self._shouldMove:
            self._oldPath = self._glyph.getRepresentation(
                "defconQt.NoComponentsQPainterPath"
            )
        widget.update()

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton:
            super().mouseMoveEvent(event)
            return
        if self._origin is None:
            return
        glyph = self._glyph
        widget = self.parent()
        if self._shouldMove or self._mouseItem is not None:
            canvasPos = event.pos()
            modifiers = event.modifiers()
            if modifiers & Qt.ShiftModifier:
                # we clamp to the mouseDownPos, unless we have a
                # single offCurve in which case we clamp it against
                # its parent
                canvasPos = self.clampToOrigin(canvasPos, self._origin)
                if isinstance(self._mouseItem, tuple):
                    selection = glyph.selection
                    if len(selection) == 1:
                        c, i = self._mouseItem
                        p_ = c[i]
                        if p_.segmentType is None:
                            for d in (-1, 1):
                                p__ = c.getPoint(i + d)
                                if p__.segmentType is not None:
                                    canvasPos = self.clampToOrigin(
                                        canvasPos, QPointF(p__.x, p__.y)
                                    )
                                    p_.x = canvasPos.x()
                                    p_.y = canvasPos.y()
                                    c.dirty = True
                                    return
            dx = canvasPos.x() - self._prevPos.x()
            dy = canvasPos.y() - self._prevPos.y()
            kwargs = dict()
            if modifiers == platformSpecific.combinedModifiers():
                kwargs["nudgePoints"] = True
            elif modifiers & Qt.AltModifier:
                kwargs["slidePoints"] = True
            moveUIGlyphElements(glyph, dx, dy, **kwargs)
            self._prevPos = canvasPos
        else:
            canvasPos = event.localPos()
            self._rubberBandRect = QRectF(self._origin, canvasPos).normalized()
            items = widget.items(self._rubberBandRect)
            points = {c[i] for c, i in items["points"]}
            if event.modifiers() & Qt.ControlModifier:
                points ^= self._oldSelection
            # TODO: fine-tune this more, maybe add optional args to items...
            if event.modifiers() & Qt.AltModifier:
                points = {pt for pt in points if pt.segmentType}
            if points != self._glyph.selection:
                # TODO: doing this takes more time than by-contour
                # discrimination for large point count
                glyph.selection = points
        widget.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # we changed glyph during this mouse press, skip special
            # processing,
            # (this would be a no-op except for unbalanced undo warning)
            if hasattr(self, "_switched"):
                del self._switched
            else:
                self._maybeJoinContour(event.localPos())
                self._glyph.endUndoGroup()
            self._mouseItem = None
            self._oldPath = None
            self._oldSelection = set()
            self._rubberBandRect = None
            self._shouldMove = False
            self.parent().update()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        widget = self.parent()
        self._mouseItem = item = widget.itemAt(self._origin)
        self._glyph.beginUndoGroup()
        if item is not None:
            if isinstance(item, tuple):
                contour, index = item
                point = contour[index]
                if point.segmentType is not None:
                    if all(contour.getPoint(index + d).segmentType for d in (-1, 1)):
                        return
                    point.smooth = not point.smooth
                    contour.dirty = True
                    # if we have one offCurve, make it tangent
                    maybeProjectUISmoothPointOffcurve(contour, index)
            elif isinstance(item, (Anchor, Guideline)):
                self._editItem(item)
        else:
            if self._performSegmentClick(event.localPos(), "selectContour"):
                return
            index = widget.indexForPoint(widget.mapFromCanvas(event.localPos()))
            if index is not None:
                # we're about to switch glyph, end undo group first
                self._glyph.endUndoGroup()
                self._switched = True
                widget.setActiveIndex(index)
        # don't perform move events on double click
        self._origin = None

    # custom painting

    def paintBackground(self, painter, index):
        if index != self.parent().activeIndex():
            return
        if self._oldPath is not None:
            # XXX: honor partialAliasing
            painter.save()
            pen = painter.pen()
            pen.setColor(QColor(210, 210, 210))
            pen.setWidth(0)
            painter.setPen(pen)
            painter.drawPath(self._oldPath)
            painter.restore()

    def paint(self, painter, index):
        if self._rubberBandRect is None:
            return
        widget = self.parent()
        if index != widget.activeIndex():
            return
        rect = self._rubberBandRect
        if platformSpecific.useBuiltinRubberBand():
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
            widget.style().drawControl(QStyle.CE_RubberBand, option, painter, widget)
            painter.restore()
        else:
            highlight = widget.palette().color(QPalette.Active, QPalette.Highlight)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, False)
            pen = painter.pen()
            pen.setColor(highlight.darker(120))
            pen.setWidth(0)
            painter.setPen(pen)
            highlight.setAlphaF(0.35)
            painter.setBrush(highlight)
            painter.drawRect(rect)
            painter.restore()
