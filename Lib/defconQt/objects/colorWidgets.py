from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QColorDialog, QStyle, QStyleOptionFrame,
                             QStylePainter, QWidget)


class ColorVignette(QWidget):
    """
    A widget that presents a color in the form of a vignette. Opens up a color
    picker dialog upon double click unless readOnly is set to True.

    Inspired by ColorPreview and ColorSelector, by Mattia Basaglia.
    """

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self._color = color
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
        dialog = QColorDialog()
        ok = dialog.exec_()
        if ok:
            self.setColor(dialog.currentColor())

    def readOnly(self):
        return self._readOnly

    def setReadOnly(self, value):
        self._readOnly = value

    def paint(self, painter, rect):
        panel = QStyleOptionFrame()
        panel.initFrom(self)
        panel.lineWidth = 2
        panel.midLineWidth = 0
        panel.rect = panel.rect.adjusted(2, 2, -2, -2)
        panel.state = panel.state | QStyle.State_Sunken
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
