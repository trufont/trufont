from math import copysign
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsItem, QStyleOptionGraphicsItem,
    QStyle, QApplication)
from PyQt5.QtGui import QBrush, QPen, QColor
from defconQt.util.roundPosition import roundPosition

offCurvePointColor = QColor.fromRgbF(1, 1, 1, 1)
offCurvePointStrokeColor = QColor.fromRgbF(.6, .6, .6, 1)
pointSelectionColor = Qt.red

offCurvePointSize = 8  # 5
offWidth = offHeight = roundPosition(offCurvePointSize)
# * self._inverseScale)
offHalf = offWidth / 2.0
offCurvePenWidth = 1.0


class OffCurvePointItem(QGraphicsEllipseItem):

    def __init__(self, x, y, parent=None):
        super(OffCurvePointItem, self).__init__(parent)
        # since we have a parent, setPos must be relative to it
        self.setPointPath()
        # TODO: abstract and use pointX-self.parent().pos().x()
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)

        self.setBrush(QBrush(offCurvePointColor))
        self._needsUngrab = False

    def delete(self):
        self.parentItem()._CPDeleted(self)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
            if QApplication.keyboardModifiers() & Qt.ShiftModifier \
                    and len(self.scene().selectedItems()) == 1:
                ax = abs(value.x())
                ay = abs(value.y())
                if ay >= ax * 2:
                    value.setX(0)
                elif ay > ax / 2:
                    avg = (ax + ay) / 2
                    value.setX(copysign(avg, value.x()))
                    value.setY(copysign(avg, value.y()))
                else:
                    value.setY(0)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.parentItem()._CPMoved(self, value)
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            self.parentItem()._CPSelected(self, value)
        return value

    def mousePressEvent(self, event):
        if not self._needsUngrab and self.x() == 0 and self.y() == 0:
            event.ignore()
        super(OffCurvePointItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super(OffCurvePointItem, self).mouseReleaseEvent(event)
        if self._needsUngrab:
            self.ungrabMouse()
            self._needsUngrab = False

    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        # if self.x() == 0 and self.y() == 0: return
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        pen = self.pen()
        if option.state & QStyle.State_Selected:
            pen.setColor(pointSelectionColor)
        else:
            pen.setColor(offCurvePointStrokeColor)
        self.setPen(pen)
        super(OffCurvePointItem, self).paint(painter, newOption, widget)

    def setPointPath(self, scale=None):
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
        self.prepareGeometryChange()
        self.setRect(-offHalf / scale, -offHalf / scale,
                     offWidth / scale, offHeight / scale)
        self.setPen(QPen(offCurvePointStrokeColor, offCurvePenWidth / scale))
