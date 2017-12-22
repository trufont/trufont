from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QApplication
from trufont.drawingTools.baseTool import BaseTool
from trufont.tools.uiMethods import moveUIPoint

_path = QPainterPath()
_path.moveTo(5.0, 5.0)
_path.lineTo(5.0, 25.0)
_path.lineTo(25.0, 25.0)
_path.lineTo(25.0, 5.0)
_path.lineTo(5.0, 5.0)
_path.closeSubpath()

class ShapesTool(BaseTool):
    icon = _path
    name = QApplication.translate("ShapesTool", "Shapes")
    shortcut = "S"

    def __init__(self, parent=None):
        super().__init__(parent)

    # events
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        #self._glyph.beginUndoGroup()
        self._origin = event.localPos()
        widget = self.parent()
        #candidate = self._getSelectedCandidatePoint()
        mouseItem = widget.itemAt(self._origin)

        canvasPos = event.pos()
        x, y = canvasPos.x(), canvasPos.y()

        # Create a new contour
        contour = self._glyph.instantiateContour()
        self._glyph.appendContour(contour)
        # point
        pointType = "line"
        # Unselect all points (*click*) and enable new point
        self._glyph.selected = False
        contour.addPoint((x, y), pointType)
        contour.addPoint((x, y-64), pointType)
        contour.addPoint((x-64, y-64), pointType)
        contour.addPoint((x-64, y), pointType)
        contour[-1].selected = True
        contour.postNotification(
            notification="Contour.SelectionChanged")
        self._targetContour = contour

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton:
            super().mouseMoveEvent(event)
            return

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._shouldMoveOnCurve = False
            self._stashedOffCurve = None
            self._targetContour = None
            self._glyph.endUndoGroup()
        else:
            super().mouseReleaseEvent(event)
