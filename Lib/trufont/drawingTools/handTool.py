from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QApplication
from trufont.drawingTools.baseTool import BaseTool


_path = QPainterPath()
_path.moveTo(12.5, 22.6)
_path.lineTo(16.3, 18.5)
_path.lineTo(15.7, 17.9)
_path.lineTo(10.3, 23.8)
_path.cubicTo(9.8, 24.4, 9.1, 24.4, 8.7, 24.1)
_path.cubicTo(8.1, 23.6, 8.2, 23, 8.7, 22.4)
_path.lineTo(13.7, 17.2)
_path.lineTo(13, 16.5)
_path.lineTo(7.3, 22.5)
_path.cubicTo(6.8, 23.1, 6.2, 23.2, 5.7, 22.7)
_path.cubicTo(5.1, 22.3, 5.2, 21.6, 5.6, 21.1)
_path.lineTo(11.6, 14.8)
_path.lineTo(10.9, 14.1)
_path.lineTo(6.2, 19.1)
_path.cubicTo(5.7, 19.6, 5.1, 19.8, 4.5, 19.3)
_path.cubicTo(4, 18.8, 4, 18.1, 4.5, 17.5)
_path.lineTo(11.2, 10.3)
_path.lineTo(7.9, 10.9)
_path.cubicTo(6.9, 11, 6.4, 10.7, 6.3, 10.1)
_path.cubicTo(6, 9.3, 6.7, 8.7, 7.6, 8.1)
_path.cubicTo(9.3, 7.2, 12.6, 6, 14.3, 5.7)
_path.cubicTo(16.7, 5.2, 19, 5.7, 21.1, 7.6)
_path.cubicTo(23.7, 10, 24, 13.5, 21.5, 16.1)
_path.lineTo(14.2, 24.1)
_path.cubicTo(13.8, 24.6, 13, 24.8, 12.4, 24.2)
_path.cubicTo(12, 23.8, 12, 23, 12.5, 22.6)
_path.closeSubpath()


class HandTool(BaseTool):

    icon = _path
    name = QApplication.translate("HandTool", "Hand")
    shortcut = "H"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            widget = self.parent()
            widget.setCursor(Qt.ClosedHandCursor)
            self._panOrigin = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, "_panOrigin"):
            pos = event.globalPos()
            self.parent().scrollBy(pos - self._panOrigin)
            self._panOrigin = pos

    def mouseReleaseEvent(self, event):
        widget = self.parent()
        widget.setCursor(Qt.OpenHandCursor)
        if hasattr(self, "_panOrigin"):
            del self._panOrigin

    @property
    def cursor(self):
        return Qt.OpenHandCursor
