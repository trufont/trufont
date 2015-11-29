from PyQt5.QtWidgets import QGraphicsItem, QGraphicsSimpleTextItem
from PyQt5.QtGui import QColor

#TODO: DRY this:
metricsColor = QColor(70, 70, 70)


class VGuidelinesTextItem(QGraphicsSimpleTextItem):

    def __init__(self, text, font, parent=None):
        super(VGuidelinesTextItem, self).__init__(text, parent)
        self.setBrush(metricsColor)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFont(font)
