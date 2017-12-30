from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainter, QPalette, QPainterPath
from PyQt5.QtWidgets import (
    QRubberBand, QStyle, QStyleOptionRubberBand, QApplication)
from trufont.drawingTools.baseTool import BaseTool
from trufont.tools import platformSpecific

# Draw icon
_path = QPainterPath()
_path.setFillRule(Qt.WindingFill)
_path.addRect(6, 14, 10, 10)
_path.addEllipse(12, 6, 12, 12)


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

    # Actions performed when a mouse button is pressed
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._glyph.beginUndoGroup()

        # Set a point to start drawing the shape
        self._startPoint = event.localPos()

    # Actions performed when a mouse button is held down
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        # Display a temporary guide showing the bounds of the shape
        widget = self.parent()
        self._rubberBandRect = QRectF(
            self._startPoint, event.localPos()).normalized()
        widget.update()

    # Actions performed when a mouse button is released
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._rubberBandRect = None

        # Set a point marking the end point of the shape
        self._endPoint = event.localPos()

        # Get points to construct the shape
        endX, endY = self._endPoint.x(), self._endPoint.y()
        startX, startY = self._startPoint.x(), self._startPoint.y()

        # Create a new contour
        contour = self._glyph.instantiateContour()
        self._glyph.appendContour(contour)
        pointType = "line"
        self._glyph.selected = False

        # Draw ellipse if right mouse button was pressed
        if event.button() == Qt.RightButton:
            midX = (startX + endX) / 2
            midY = (startY + endY) / 2
            handleXStart = (midX + startX) / 2
            handleXEnd = (midX + endX) / 2
            handleYStart = (midY + startY) / 2
            handleYEnd = (midY + endY) / 2

            contour.addPoint((midX, startY), segmentType="curve", smooth=True)
            contour.addPoint((handleXEnd, startY))
            contour.addPoint((endX, handleYStart))
            contour.addPoint((endX, midY), segmentType="curve", smooth=True)
            contour.addPoint((endX, handleYEnd))
            contour.addPoint((handleXEnd, endY))
            contour.addPoint((midX, endY), segmentType="curve", smooth=True)
            contour.addPoint((handleXStart, endY))
            contour.addPoint((startX, handleYEnd))
            contour.addPoint((startX, midY), segmentType="curve", smooth=True)
            contour.addPoint((startX, handleYStart))
            contour.addPoint((handleXStart, startY))
            contour[0].selected = True

        # Else, draw a rectangle
        else:
            contour.addPoint((startX, startY), pointType)
            contour.addPoint((startX, endY), pointType)
            contour.addPoint((endX, endY), pointType)
            contour.addPoint((endX, startY), pointType)
            contour[0].selected = True

        self._glyph.endUndoGroup()

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
