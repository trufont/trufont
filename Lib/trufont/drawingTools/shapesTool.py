from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPalette, QPainterPath
from PyQt5.QtWidgets import (
    QRubberBand, QStyle, QStyleOptionRubberBand, QApplication)
from defcon import Glyph
from trufont.drawingTools.baseTool import BaseTool
from trufont.tools import bezierMath, platformSpecific

# Draw icon
_path = QPainterPath()
_path.addRect(4, 14, 14, 14)
_path.addEllipse(10, 6, 16, 16)


class ShapesTool(BaseTool):
    """
    A tool for generating basic geometric shapes.
    """
    icon = _path
    name = QApplication.translate("ShapesTool", "Shapes")
    shortcut = "S"

    # Initialize attributes when class is invoked
    def __init__(self, parent=None):
        super().__init__(parent)
        self._startPoint = None
        self._endPoint = None
        self._rubberBandRect = None

    # Events

    # Actions performed when a mouse button is released
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._startPoint = event.localPos()

    # Actions performed when a mouse button is pressed and dragging takes place
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        widget = self.parent()
        self._rubberBandRect = QRectF(
            self._startPoint, event.localPos()).normalized()
        widget.update()

    # Actions performed when a mouse button is released
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._endPoint = event.localPos()
        self._rubberBandRect = None

        # Get points to construct shape
        endX, endY = self._endPoint.x(), self._endPoint.y()
        startX, startY = self._startPoint.x(), self._startPoint.y()

        # Create a new contour
        contour = self._glyph.instantiateContour()
        self._glyph.appendContour(contour)
        pointType = "line"
        self._glyph.selected = False

        # Draw Shape
        contour.addPoint((startX, startY), pointType)
        contour.addPoint((startX, endY), pointType)
        contour.addPoint((endX, endY), pointType)
        contour.addPoint((endX, startY), pointType)
        contour[0].selected = True

    def paint(self, painter, index):
        if self._rubberBandRect is None:
            return
        widget = self.parent()
        if index != widget.activeIndex():
            return
        rect = self._rubberBandRect
        if platformSpecific.useBuiltinRubberBand():
            # okay, OS-native rubber band does not support painting with
            # floating-point coordinates
            # paint directly on the widget with unscaled context
            widgetOrigin = widget.mapFromCanvas(rect.bottomLeft())
            widgetMove = widget.mapFromCanvas(rect.topRight())
            option = QStyleOptionRubberBand()
            option.initFrom(widget)
            option.opaque = False
            option.rect = QRectF(widgetOrigin, widgetMove).toRect()
            option.shape = QRubberBand.Rectangle
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.resetTransform()
            widget.style().drawControl(
                QStyle.CE_RubberBand, option, painter, widget)
            painter.restore()
        else:
            highlight = widget.palette(
                ).color(QPalette.Active, QPalette.Highlight)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, False)
            pen = painter.pen()
            pen.setColor(highlight.darker(120))
            pen.setWidth(0)
            painter.setPen(pen)
            highlight.setAlphaF(.35)
            painter.setBrush(highlight)
            painter.drawRect(rect)
            painter.restore()
