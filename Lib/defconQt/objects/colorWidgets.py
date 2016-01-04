from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QColorDialog, QStyle, QStyleOptionFrame, QStylePainter, QWidget)

strikeColor = QColor(170, 0, 0)


class ColorVignette(QWidget):
    """
    A widget that presents a color in the form of a vignette. Opens up a color
    picker dialog upon double click unless readOnly is set to True.

    Inspired by ColorPreview and ColorSelector, by Mattia Basaglia.
    """

    colorChanged = pyqtSignal()

    # TODO: consider painting on hover like QLineEdit
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = None
        self._margins = (0, 2, 0, -2)
        self._mayClearColor = True
        self._readOnly = False

    def color(self):
        return self._color

    def setColor(self, color):
        self._color = color
        self.update()

    def mayClearColor(self):
        return self._mayClearColor

    def setMayClearColor(self, value):
        self._mayClearColor = value

    def mousePressEvent(self, event):
        if self._mayClearColor and event.modifiers() & Qt.AltModifier:
            self.setColor(None)

    def mouseDoubleClickEvent(self, event):
        if self._readOnly:
            return
        dialog = QColorDialog(self._color)
        dialog.setOptions(QColorDialog.ShowAlphaChannel)
        ok = dialog.exec_()
        if ok:
            self.setColor(dialog.currentColor())
            self.colorChanged.emit()

    def margins(self):
        dx1, dy1, dx2, dy2 = self._margins
        return (dx1, dy1, -dx2, -dy2)

    def setMargins(self, left, top, right, bottom):
        self._margins = (left, top, -right, -bottom)

    def readOnly(self):
        return self._readOnly

    def setReadOnly(self, value):
        self._readOnly = value

    def paint(self, painter, rect):
        panel = QStyleOptionFrame()
        panel.initFrom(self)
        panel.lineWidth = 2
        panel.midLineWidth = 0
        panel.rect = panel.rect.adjusted(*self._margins)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Frame, panel, painter, self)
        rect = style.subElementRect(QStyle.SE_FrameContents, panel, self)
        painter.fillRect(rect, Qt.white)
        innerRect = rect.adjusted(2, 2, -2, -2)
        if self._color is not None:
            painter.fillRect(innerRect, self._color)
        else:
            pen = painter.pen()
            pen.setColor(strikeColor)
            pen.setWidthF(1.5)
            painter.setPen(pen)
            painter.setRenderHint(QStylePainter.Antialiasing)
            painter.setClipRect(innerRect)
            bL = innerRect.bottomLeft()
            bL.setY(bL.y() + .5)
            tR = innerRect.topRight()
            tR.setY(tR.y() + 1)
            painter.drawLine(bL, tR)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        self.paint(painter, self.geometry())

    def resizeEvent(self, event):
        self.update()

    def sizeHint(self):
        return QSize(24, 24)
