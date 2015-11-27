from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtWidgets import (QColorDialog, QStyle, QStyleOptionFrame,
                             QStylePainter, QWidget)


class ColorVignette(QWidget):
    """
    A widget that presents a color in the form of a vignette. Opens up a color
    picker dialog upon double click unless readOnly is set to True.

    Inspired by ColorPreview and ColorSelector, by Mattia Basaglia.
    """

    colorChanged = pyqtSignal()

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self._color = color
        self._margins = (0, 2, 0, -2)
        self._readOnly = False

    def color(self):
        return self._color

    def setColor(self, color):
        self._color = color
        self.update()

    def mouseDoubleClickEvent(self, event):
        event.accept()
        if self._readOnly:
            return
        dialog = QColorDialog(self._color)
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
        self.style().drawPrimitive(QStyle.PE_Frame, panel, painter, self)
        r = self.style().subElementRect(QStyle.SE_FrameContents, panel, self)
        painter.fillRect(r, Qt.white)
        painter.fillRect(r.adjusted(2, 2, -2, -2), self._color)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        self.paint(painter, self.geometry())

    def resizeEvent(self, event):
        self.update()

    def sizeHint(self):
        return QSize(24, 24)
