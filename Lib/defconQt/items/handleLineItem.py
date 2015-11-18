from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsLineItem

bezierHandleColor = QColor.fromRgbF(0, 0, 0, .2)

class HandleLineItem(QGraphicsLineItem):

    def __init__(self, x1, y1, x2, y2, parent):
        super(HandleLineItem, self).__init__(x1, y1, x2, y2, parent)
        self.setPen(QPen(bezierHandleColor, 1.0))
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)