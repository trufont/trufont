from PyQt5.QtCore import QObject
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication


class BaseTool(QObject):
    name = QApplication.translate("BaseTool", "Tool")
    cursor = QCursor()
    iconPath = None

    def __init__(self, parent=None):
        super().__init__(parent)

    def toolActivated(self):
        pass

    def toolDisabled(self):
        pass

    @property
    def _glyph(self):
        return self.parent().glyph()

    # helper functions

    def clampToOrigin(self, pos, origin):
        deltaX = pos.x() - origin.x()
        deltaY = pos.y() - origin.y()
        # go into the first quadrant to simplify our study
        aDeltaX = abs(deltaX)
        aDeltaY = abs(deltaY)
        # diagonal incr.
        # if aDeltaY >= aDeltaX * 2:
        #     pos.setX(origin.x())
        # elif aDeltaY > aDeltaX / 2:
        #     avg = (aDeltaX + aDeltaY) / 2
        #     pos.setX(origin.x() + copysign(avg, deltaX))
        #     pos.setY(origin.y() + copysign(avg, deltaY))
        if aDeltaY >= aDeltaX:
            pos.setX(origin.x())
        else:
            pos.setY(origin.y())
        return pos

    def magnetPos(self, pos):
        widget = self.parent()
        itemTuple = widget.itemAt(pos)
        if itemTuple is not None:
            itemUnderMouse, parent = itemTuple
            if parent is not None:
                pos.setX(itemUnderMouse.x)
                pos.setY(itemUnderMouse.y)
        return pos

    # events

    def keyPressEvent(self, event):
        pass

    def keyReleaseEvent(self, event):
        pass

    def mousePressEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass

    def mouseDoubleClickEvent(self, event):
        pass

    # custom painting

    def paint(self, painter):
        pass
