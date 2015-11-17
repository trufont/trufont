from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PyQt5.QtGui import QTransform

class ComponentItem(QGraphicsPathItem):

    def __init__(self, path, component, parent=None):
        super(ComponentItem, self).__init__(path, parent)
        self._component = component
        self.setTransform(QTransform(*component.transformation))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def delete(self):
        glyph = self._component.getParent()
        glyph.removeComponent(self._component)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
        elif change == QGraphicsItem.ItemPositionHasChanged:
            t = self._component.transformation
            x = self.pos().x()
            y = self.pos().y()
            scene = self.scene()
            scene._blocked = True
            self._component.transformation = (t[0], t[1], t[2], t[3], x, y)
            scene._blocked = False
        return value
