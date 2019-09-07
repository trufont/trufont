from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainter, QPainterPath, QPalette
from PyQt5.QtWidgets import QApplication, QRubberBand, QStyle, QStyleOptionRubberBand

from trufont.drawingTools.baseTool import BaseTool
from trufont.tools import platformSpecific

# Draw icon
_path = QPainterPath()
_path.setFillRule(Qt.WindingFill)
_path.addRect(6, 14, 10, 10)
_path.addEllipse(12, 6, 12, 12)


class ShapesTool(BaseTool):
    icon = _path
    name = QApplication.translate("ShapesTool", "Shapes")
    shortcut = "S"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._startPoint = None
        self._endPoint = None
        self._rubberBandRect = None

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._glyph.beginUndoGroup()
        self._startPoint = event.localPos()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        widget = self.parent()
        self._endPoint = event.localPos()

        # Get the width of the shape
        width = abs(int(self._endPoint.x() - self._startPoint.x()))

        # If Shift key is pressed, equalize the width and height of the shape
        if event.modifiers() & Qt.ShiftModifier:
            if self._startPoint.y() >= self._endPoint.y():
                self._endPoint.setY(int(self._startPoint.y() - width))
            else:
                self._endPoint.setY(int(self._startPoint.y() + width))

        # Draw a temporary shape guide
        self._rubberBandRect = QRectF(self._startPoint, self._endPoint)
        widget.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        # Remove the temporary shape guide
        self._rubberBandRect = None

        # Create a new contour
        contour = self._glyph.instantiateContour()
        self._glyph.appendContour(contour)
        self._glyph.selected = False

        # Get points to construct the new shape contour
        endX, endY = int(self._endPoint.x()), int(self._endPoint.y())
        startX, startY = int(self._startPoint.x()), int(self._startPoint.y())

        # Draw ellipse if right mouse button was pressed
        if event.button() == Qt.RightButton:
            handlePos = 0.55
            midX = (endX + startX) / 2
            midY = (endY + startY) / 2
            halfWidthX = (endX - startX) / 2
            halfWidthY = (endY - startY) / 2
            handleXStart = midX - halfWidthX * handlePos
            handleXEnd = midX + halfWidthX * handlePos
            handleYStart = midY - halfWidthY * handlePos
            handleYEnd = midY + halfWidthY * handlePos

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
            contour.addPoint((startX, startY), "line")
            contour.addPoint((startX, endY), "line")
            contour.addPoint((endX, endY), "line")
            contour.addPoint((endX, startY), "line")
            contour[0].selected = True

        self._glyph.endUndoGroup()

    # Draw the graphics on screen
    def paint(self, painter, index):
        if self._rubberBandRect is None:
            return
        widget = self.parent()
        if index != widget.activeIndex():
            return
        rect = self._rubberBandRect
        if platformSpecific.useBuiltinRubberBand():
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
            widget.style().drawControl(QStyle.CE_RubberBand, option, painter, widget)
            painter.restore()
        else:
            highlight = widget.palette().color(QPalette.Active, QPalette.Highlight)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, False)
            pen = painter.pen()
            pen.setColor(highlight.darker(120))
            pen.setWidth(0)
            painter.setPen(pen)
            highlight.setAlphaF(0.35)
            painter.setBrush(highlight)
            painter.drawRect(rect)
            painter.restore()
