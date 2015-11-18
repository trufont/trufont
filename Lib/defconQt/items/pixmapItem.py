from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt5.QtGui import QTransform
from defconQt.objects.sizeGripItem import SizeGripItem

class PixmapItem(QGraphicsPixmapItem):

    def __init__(self, x, y, pixmap, scale, parent=None):
        super(QGraphicsPixmapItem, self).__init__(pixmap, parent)
        self._pixmap = pixmap
        self.setOffset(x, -y)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)
        self.setTransform(QTransform().fromScale(1, -1))
        self.setOpacity(.6)
        self.setZValue(-1)
        sizeGripItem = SizeGripItem(scale, self)
        sizeGripItem.setVisible(False)

    def setRect(self, rect):
        dTopLeft = rect.topLeft() - self.pos()
        if not dTopLeft.isNull():
            self.setOffset(dTopLeft)
        self.setPixmap(self._pixmap.scaled(
            rect.size().toSize()
        ))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            sizeGripItem = self.childItems()[0]
            sizeGripItem.setVisible(value)
        return value
