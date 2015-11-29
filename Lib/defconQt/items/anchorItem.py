from defconQt.util.roundPosition import roundPosition
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGraphicsPathItem, QGraphicsSimpleTextItem,
    QGraphicsItem, QStyleOptionGraphicsItem, QStyle)
from PyQt5.QtGui import (
    QColor, QFont, QBrush, QPen, QPainterPath)

from defconQt.dialogs.addAnchorDialog import AddAnchorDialog

anchorColor = QColor(120, 120, 255)
anchorSelectionColor = Qt.blue
anchorSize = 11
anchorWidth = anchorHeight = roundPosition(anchorSize)
anchorHalf = anchorWidth / 2.0


class AnchorItem(QGraphicsPathItem):

    def __init__(self, anchor, scale=1, parent=None):
        super(AnchorItem, self).__init__(parent)
        self._anchor = anchor

        textItem = QGraphicsSimpleTextItem(self._anchor.name, parent=self)
        font = QFont()
        font.setPointSize(9)
        textItem.setFont(font)
        textItem.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setPointPath(scale)
        self.setPos(self._anchor.x, self._anchor.y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(anchorColor))
        self.setPen(QPen(Qt.NoPen))

    def delete(self):
        glyph = self._anchor.getParent()
        glyph.removeAnchor(self._anchor)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
        elif change == QGraphicsItem.ItemPositionHasChanged:
            x = self.pos().x()
            y = self.pos().y()
            scene = self.scene()
            scene._blocked = True
            self._anchor.x = x
            self._anchor.y = y
            scene._blocked = False
        return value

    def mouseDoubleClickEvent(self, event):
        view = self.scene().views()[0]
        newAnchorName, ok = AddAnchorDialog.getNewAnchorName(view)
        if ok:
            self._anchor.name = newAnchorName

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

        path.moveTo(-anchorHalf / scale, 0)
        path.lineTo(0, anchorHalf / scale)
        path.lineTo(anchorHalf / scale, 0)
        path.lineTo(0, -anchorHalf / scale)
        path.closeSubpath()

        self.prepareGeometryChange()
        self.setPath(path)
        textItem = self.childItems()[0]
        textItem.setPos(anchorHalf / scale,
                        textItem.boundingRect().height() / 2)

    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        if option.state & QStyle.State_Selected:
            self.setBrush(anchorSelectionColor)
        else:
            self.setBrush(anchorColor)
        super(AnchorItem, self).paint(painter, newOption, widget)
