"""
The *colorVignette* submodule
-----------------------------
"""

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QColorDialog,
    QSizePolicy,
    QStyle,
    QStyleOptionFrame,
    QStylePainter,
    QWidget,
)

strikeColor = QColor(144, 60, 74)


class ColorVignette(QWidget):
    """
    A QWidget_ that presents a color in the form of a vignette. Opens up a
    color picker dialog upon double click (or Return key with focus set),
    unless *readOnly* is set to True.
    If *mayClearColor* is True, the color may be cleared with Alt-click (or
    Alt-Return with focus).

    Inspired by ColorPreview and ColorSelector by Mattia Basaglia.

    .. _QWidget: http://doc.qt.io/qt-5/qwidget.html
    """

    colorChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self._color = None
        self._margins = (0, 2, 0, -2)
        self._mayClearColor = True
        self._readOnly = False

    def pickColor(self):
        """
        Opens up a modal QColorDialog_ to choose a new color, and stores it in
        this widget if the user clicks on the Ok button.
        Emits *colorChanged* when successful.

        .. _QColorDialog: http://doc.qt.io/qt-5/qcolordialog.html
        """
        if self._readOnly:
            return
        dialog = QColorDialog(self._color)
        dialog.setOptions(QColorDialog.ShowAlphaChannel)
        ok = dialog.exec_()
        if ok:
            self.setColor(dialog.currentColor())
            self.colorChanged.emit()

    # attributes

    def color(self):
        """
        Returns the color displayed by this widget, or None if no color
        is displayed.
        """
        return self._color

    def setColor(self, color):
        """
        Sets this widget’s QColor_ to *color*.

        The default is None.

        .. _QColor: http://doc.qt.io/qt-5/qcolor.html
        """
        self._color = color
        self.update()

    def margins(self):
        """
        Returns the margins of this widget’s color rectangle as a tuple of four
        scalars.
        """
        dx1, dy1, dx2, dy2 = self._margins
        return (dx1, dy1, -dx2, -dy2)

    def setMargins(self, left, top, right, bottom):
        """
        Sets the margins of the color rectangle inside this widget to *(left,
        top, right, bottom)*.

        The default is (0, 2, 0, 2).
        """
        self._margins = (left, top, -right, -bottom)
        self.update()

    def mayClearColor(self):
        """
        Returns whether this widget allows *color* be set to None by user
        input.
        """
        return self._mayClearColor

    def setMayClearColor(self, value):
        """
        Sets whether the user can clear the color.
        """
        self._mayClearColor = value

    def readOnly(self):
        """
        Returns whether this widget is read-only.
        """
        return self._readOnly

    def setReadOnly(self, value):
        """
        Sets whether this widget should be read-only. If *value* is true,
        :func:`pickColor` will have no effect.
        """
        self._readOnly = value
        self.update()

    # events

    def keyPressEvent(self, event):
        if event.key() & Qt.Key_Return:
            if self._mayClearColor and event.modifiers() & Qt.AltModifier:
                self.setColor(None)
            else:
                self.pickColor()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if self._mayClearColor and event.modifiers() & Qt.AltModifier:
            self.setColor(None)
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.pickColor()

    def initStyleOption(self, option):
        option.initFrom(self)
        option.lineWidth = self.style().pixelMetric(
            QStyle.PM_DefaultFrameWidth, option, self
        )
        option.midLineWidth = 0
        option.rect = option.rect.adjusted(*self._margins)
        option.state |= QStyle.State_Sunken
        if self._readOnly:
            option.state |= QStyle.State_ReadOnly

    def paint(self, painter, rect):
        panel = QStyleOptionFrame()
        self.initStyleOption(panel)
        style = self.style()
        # use PE_PanelLineEdit instead of static PE_Frame to have hover/focus
        # animation
        style.drawPrimitive(QStyle.PE_PanelLineEdit, panel, painter, self)
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
            bL.setY(bL.y() + 0.5)
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
