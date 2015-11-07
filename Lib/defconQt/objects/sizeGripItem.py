# SizeGripItem - A size grip QGraphicsItem for interactive resizing.
#
# Python port by Felipe Correa da Silva Sanches
# based on the original C++ code by Cesar L. B. Silveira
#
# Copyright 2011, Cesar L. B. Silveira.
# Copyright 2015, Felipe Correa da Silva Sanches <juca@members.fsf.org>.
# Copyright 2015, Adrien Tétar.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPen
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem

Top = 1 << 0
Bottom = 1 << 1
Left = 1 << 2
Right = 1 << 3
Center = 1 << 4
TopLeft = Top | Left
BottomLeft = Bottom | Left
TopRight = Top | Right
BottomRight = Bottom | Right

possibleFlags = (Top, Bottom, Left, TopLeft, BottomLeft, Right, TopRight,
                 BottomRight, Center)


class ResizeHandleItem(QGraphicsRectItem):
    def __init__(self, positionFlags, scale, parent):
        super(ResizeHandleItem, self).__init__(parent)
        self.setPointPath(scale)
        self.positionFlags = positionFlags
        self.setBrush(QBrush(Qt.lightGray))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        if self.positionFlags in (Top, Bottom):
            cursor = Qt.SizeVerCursor
        elif self.positionFlags in (Left, Right):
            cursor = Qt.SizeHorCursor
        elif self.positionFlags in (BottomLeft, TopRight):
            cursor = Qt.SizeBDiagCursor
        elif self.positionFlags in (TopLeft, BottomRight):
            cursor = Qt.SizeFDiagCursor
        elif self.positionFlags == Center:
            cursor = Qt.SizeAllCursor
        self.setCursor(cursor)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return self.restrictPosition(value)
        return value

    def mouseMoveEvent(self, event):
        pos = self.mapToParent(event.pos())
        parent = self.parentItem()
        if self.positionFlags == TopLeft:
            parent.setTopLeft(pos)
        elif self.positionFlags == Top:
            parent.setTop(pos.y())
        elif self.positionFlags == TopRight:
            parent.setTopRight(pos)
        elif self.positionFlags == Right:
            parent.setRight(pos.x())
        elif self.positionFlags == BottomRight:
            parent.setBottomRight(pos)
        elif self.positionFlags == Bottom:
            parent.setBottom(pos.y())
        elif self.positionFlags == BottomLeft:
            parent.setBottomLeft(pos)
        elif self.positionFlags == Left:
            parent.setLeft(pos.x())
        elif self.positionFlags == Center:
            parent.setCenter(pos)
        parent.doResize()

    def restrictPosition(self, newPos):
        parent = self.parentItem()
        retVal = newPos

        if self.positionFlags & Top or self.positionFlags & Bottom:
            retVal.setY(newPos.y())
        if self.positionFlags & Left or self.positionFlags & Right:
            retVal.setX(newPos.x())

        if self.positionFlags & Top and retVal.y() > parent.rect.bottom():
            retVal.setY(parent.rect.bottom())
        elif self.positionFlags & Bottom and retVal.y() < parent.rect.top():
            retVal.setY(parent.rect.top())

        if self.positionFlags & Left and retVal.x() > parent.rect.right():
            retVal.setX(parent.rect.right())
        elif self.positionFlags & Right and retVal.x() < parent.rect.left():
            retVal.setX(parent.rect.left())

        return retVal

    def setPointPath(self, scale=None):
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 4:
            scale = 4
        self.prepareGeometryChange()
        self.setPen(QPen(Qt.black, 1.0 / scale))
        self.setRect(-4 / scale, -4 / scale, 8 / scale, 8 / scale)


class SizeGripItem(QGraphicsItem):
    def __init__(self, scale, parent):
        super(SizeGripItem, self).__init__(parent)
        self.setFlag(QGraphicsItem.ItemIgnoresParentOpacity)

        for flag in possibleFlags:
            ResizeHandleItem(flag, scale, self)
        self.updateBoundingRect()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        pass

    def setTopLeft(self, pos):
        self.rect.setTopLeft(pos)

    def setTop(self, y):
        self.rect.setTop(y)

    def setTopRight(self, pos):
        self.rect.setTopRight(pos)

    def setRight(self, x):
        self.rect.setRight(x)

    def setBottomRight(self, pos):
        self.rect.setBottomRight(pos)

    def setBottom(self, y):
        self.rect.setBottom(y)

    def setBottomLeft(self, pos):
        self.rect.setBottomLeft(pos)

    def setLeft(self, x):
        self.rect.setLeft(x)

    def setCenter(self, pos):
        self.rect.moveCenter(pos)

    def doResize(self):
        self.parentItem().setRect(self.rect)
        self.updateHandleItemPositions()

    def updateBoundingRect(self):
        self.rect = self.parentItem().boundingRect()
        self.updateHandleItemPositions()

    def updateHandleItemPositions(self):
        for item in self.childItems():
            item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
            flags = item.positionFlags
            if flags == TopLeft:
                item.setPos(self.rect.topLeft())
            elif flags == Top:
                item.setPos(self.rect.left() + self.rect.width() / 2 - 1,
                            self.rect.top())
            elif flags == TopRight:
                item.setPos(self.rect.topRight())
            elif flags == Right:
                item.setPos(self.rect.right(),
                            self.rect.top() + self.rect.height() / 2 - 1)
            elif flags == BottomRight:
                item.setPos(self.rect.bottomRight())
            elif flags == Bottom:
                item.setPos(self.rect.left() + self.rect.width() / 2 - 1,
                            self.rect.bottom())
            elif flags == BottomLeft:
                item.setPos(self.rect.bottomLeft())
            elif flags == Left:
                item.setPos(self.rect.left(),
                            self.rect.top() + self.rect.height() / 2 - 1)
            elif flags == Center:
                item.setPos(self.rect.center())
            item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
