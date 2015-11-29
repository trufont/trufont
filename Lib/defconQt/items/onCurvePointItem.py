from PyQt5.QtCore import Qt, QLineF, QPointF, QEvent
from PyQt5.QtWidgets import (
    QGraphicsPathItem, QGraphicsItem, QStyleOptionGraphicsItem, QStyle)
from PyQt5.QtGui import QPainterPath, QBrush, QPen, QColor
from defconQt.util.roundPosition import roundPosition
from enum import Enum


#TODO: DRY this!
class SceneTools(Enum):
    SelectionTool = 0
    DrawingTool = 1
    RulerTool = 2
    KnifeTool = 3

onCurvePenWidth = 1.5
onCurvePointColor = QColor.fromRgbF(.6, .6, .6, 1)
onCurvePointStrokeColor = QColor.fromRgbF(1, 1, 1, 1)
onCurvePointSize = 9  # 6
onCurveSmoothPointSize = 10  # 7
onWidth = onHeight = roundPosition(onCurvePointSize)
onHalf = onWidth / 2.0
smoothWidth = smoothHeight = roundPosition(onCurveSmoothPointSize)
smoothHalf = smoothWidth / 2.0
pointSelectionColor = Qt.red


class OnCurvePointItem(QGraphicsPathItem):

    def __init__(self, x, y, isSmooth, contour, point, scale=1, parent=None):
        super(OnCurvePointItem, self).__init__(parent)
        self._contour = contour
        self._point = point
        self._isSmooth = isSmooth
        self._posBeforeMove = None

        self.setPointPath(scale)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(onCurvePointColor))

    def delete(self, preserveShape=True):
        def findNextOnCurve(self, index=0):
            for _ in self._contour:
                if self._contour[index].segmentType is not None:
                    break
                index = (index + 1) % len(self._contour)
            return index

        scene = self.scene()
        glyph = scene._glyphObject
        if len(self._contour.segments) < 2:
            glyph.removeContour(self._contour)
        else:
            ptIndex = self.getPointIndex()
            if self._contour.open and ptIndex == 0:
                nextOnCurveIndex = findNextOnCurve(self, 1)
                self._contour._points = self._contour[nextOnCurveIndex:]
                self._contour[0].segmentType = "move"
                self._contour.dirty = True
            else:
                # Using preserveShape at the edge of an open contour will
                # traceback
                if ptIndex == len(self._contour):
                    preserveShape = False
                self._contour.removeSegment(
                    self.getSegmentIndex(), preserveShape)
                nextOnCurveIndex = findNextOnCurve(self)
                self._contour.setStartPoint(nextOnCurveIndex)
        # This object will be removed from scene by notification mechanism

    def setPointPath(self, scale=None):
        path = QPainterPath()
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 4:
            scale = 4
        elif scale < .4:
            scale = .4
        if self._isSmooth:
            path.addEllipse(-smoothHalf / scale, -smoothHalf /
                            scale, smoothWidth / scale, smoothHeight / scale)
        else:
            path.addRect(-onHalf / scale, -onHalf / scale,
                         onWidth / scale, onHeight / scale)
        self.prepareGeometryChange()
        self.setPath(path)
        self.setPen(QPen(onCurvePointStrokeColor, onCurvePenWidth / scale))

    def getPointIndex(self):
        return self._contour.index(self._point)

    def getSegmentIndex(self):
        # closed contour cycles and so the "previous" segment goes to current
        # point
        index = 0 if self._contour.open else -1
        for pt in self._contour:
            if pt == self._point:
                break
            if pt.segmentType is not None:
                index += 1
        return index % len(self._contour.segments)

    def _CPDeleted(self, item):
        # XXX: is this sufficient guard?
        if self.isSelected():
            return
        pointIndex = self.getPointIndex()
        children = self.childItems()
        if item == children[1]:
            delta = -1
            segmentOn = 0
        else:
            delta = 1
            segmentOn = 3

        firstSibling = self._contour.getPoint(pointIndex + delta)
        secondSibling = self._contour.getPoint(pointIndex + delta * 2)
        if (firstSibling.segmentType is None and
                secondSibling.segmentType is None):
            # we have two offCurves, wipe them
            self._contour.getPoint(pointIndex + segmentOn).segmentType = "line"
            self._contour.removePoint(firstSibling)
            self._contour.removePoint(secondSibling)

    def _CPMoved(self, item, newValue):
        pointIndex = self.getPointIndex()
        children = self.childItems()
        # nodes are stored after lines (for stacking order)
        if item == children[1]:
            selected = 1
            propagate = 3
        else:
            selected = 3
            propagate = 1
        line = children[selected - 1].line()
        children[selected - 1].setLine(line.x1(),
                                       line.y1(), newValue.x(), newValue.y())

        if not len(children) > 4:
            elemIndex = pointIndex - 2 + selected
            self._contour.getPoint(elemIndex).x = self.pos().x() + newValue.x()
            self._contour.getPoint(elemIndex).y = self.pos().y() + newValue.y()
        if not (self._isSmooth and children[propagate].isVisible()):
            self.setShallowDirty()
            return
        if children[selected]._needsUngrab:
            targetLen = children[selected - 1].line().length() * 2
        else:
            targetLen = children[selected - 1].line().length() + \
                children[propagate - 1].line().length()
        if not newValue.isNull():
            tmpLine = QLineF(newValue, QPointF())
            tmpLine.setLength(targetLen)
        else:
            # if newValue is null, we’d construct a zero-length line and
            # collapse both offCurves
            tmpLine = QLineF(QPointF(), children[propagate].pos())
        children[propagate].setFlag(
            QGraphicsItem.ItemSendsGeometryChanges, False)
        children[propagate].setPos(tmpLine.x2(), tmpLine.y2())
        children[propagate].setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        children[propagate - 1].setLine(line.x1(),
                                        line.y1(), tmpLine.x2(), tmpLine.y2())
        propagateIn = pointIndex - 2 + propagate
        self._contour.getPoint(propagateIn).x = self.pos().x() + tmpLine.x2()
        self._contour.getPoint(propagateIn).y = self.pos().y() + tmpLine.y2()
        self.setShallowDirty()

    def _CPSelected(self, item, value):
        pointIndex = self.getPointIndex()
        children = self.childItems()
        if item == children[1]:
            delta = -1
        else:
            delta = 1

        self._contour[pointIndex + delta].selected = value

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # have a look at defcon FuzzyNumber as well
            pointIndex = self.getPointIndex()
            self._contour[pointIndex].x = self.pos().x()
            self._contour[pointIndex].y = self.pos().y()

            children = self.childItems()
            if children[1].isVisible():
                prevPos = children[1].pos()
                point = self._contour.getPoint(pointIndex - 1)
                point.x = self.pos().x() + prevPos.x()
                point.y = self.pos().y() + prevPos.y()
            if children[3].isVisible():
                nextPos = children[3].pos()
                point = self._contour.getPoint(pointIndex + 1)
                point.x = self.pos().x() + nextPos.x()
                point.y = self.pos().y() + nextPos.y()
            self.setShallowDirty()
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            self._point.selected = value
        return value

    def setShallowDirty(self):
        scene = self.scene()
        scene._blocked = True
        self._contour.dirty = True
        scene._blocked = False

    def mouseMoveEvent(self, event):
        modifiers = event.modifiers()
        children = self.childItems()
        # Ctrl: get and move prevCP, Alt: nextCP
        if (modifiers & Qt.ControlModifier and children[1].x() == 0 and
                children[1].y() == 0):
            i, o = 1, 3
        elif (modifiers & Qt.AltModifier and children[3].x() == 0 and
                children[3].y() == 0):
            i, o = 3, 1
        elif not (modifiers & Qt.ControlModifier or
                  modifiers & Qt.AltModifier):
            super(OnCurvePointItem, self).mouseMoveEvent(event)
            return
        else:  # eat the event if we are not going to yield an offCP
            event.accept()
            return
        ptIndex = self.getPointIndex()
        scene = self.scene()
        scene._blocked = True
        # if we have line segment, insert offCurve points
        insertIndex = ptIndex + (i - 1) // 2
        if self._contour.getPoint(insertIndex).segmentType == "line":
            nextToCP = self._contour.getPoint(ptIndex - 2 + i)
            assert(nextToCP.segmentType is not None)
            self._contour.getPoint(insertIndex).segmentType = "curve"
            if i == 1:
                first, second = (
                    self._point.x, self._point.y), (nextToCP.x, nextToCP.y)
            else:
                first, second = (
                    nextToCP.x, nextToCP.y), (self._point.x, self._point.y)
            self._contour.insertPoint(
                insertIndex, self._contour._pointClass(first))
            self._contour.insertPoint(
                insertIndex, self._contour._pointClass(second))
            children[i].setVisible(True)
            # TODO: need a list of items to make this efficient
            scene.getItemForPoint(nextToCP).childItems()[o].setVisible(True)
        # release current onCurve
        scene.sendEvent(self, QEvent(QEvent.MouseButtonRelease))
        scene.mouseGrabberItem().ungrabMouse()
        self.setSelected(False)
        self.setIsSmooth(False)
        children[i]._needsUngrab = True
        scene.sendEvent(children[i], QEvent(QEvent.MouseButtonPress))
        children[i].setSelected(True)
        children[i].grabMouse()
        scene._blocked = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        # XXX: meh, maybe refactor doubleClick event into the scene?
        view = self.scene().views()[0]
        if (view._currentTool == SceneTools.RulerTool or
                view._currentTool == SceneTools.KnifeTool):
            return
        self.setIsSmooth(not self._isSmooth)

    def setIsSmooth(self, isSmooth):
        self._isSmooth = isSmooth
        self._point.smooth = self._isSmooth
        self.setShallowDirty()
        self.setPointPath()

    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        pen = self.pen()
        if option.state & QStyle.State_Selected:
            pen.setColor(pointSelectionColor)
        else:
            pen.setColor(onCurvePointStrokeColor)
        self.setPen(pen)
        super(OnCurvePointItem, self).paint(painter, newOption, widget)
