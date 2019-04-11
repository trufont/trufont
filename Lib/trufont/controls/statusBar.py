from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QSpinBox, QWidget

from trufont.controls.pathButton import PathButton

__all__ = ["StatusBar"]

_minPath = QPainterPath()
_minPath.moveTo(1, 6)
_minPath.lineTo(11, 6)

_plusPath = QPainterPath(_minPath)
_plusPath.moveTo(6, 1)
_plusPath.lineTo(6, 11)

_minPath.translate(5, 7)
_plusPath.translate(5, 7)


def Button():
    btn = PathButton()
    btn.setIsDownColor(QColor(210, 210, 210))
    btn.setIsFlipped(True)
    btn.setSize(QSize(23, 25))
    return btn


class StatusBar(QWidget):
    """
    Use the *sizeChanged* signal for size changes.

    TODO: specify only isFontTab/isGlyphTab and put the details
    in the widget internals
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shouldPropagateSize = True

        self.statusLabel = QLabel(self)

        btnColor = QColor(126, 126, 126)
        minusButton = Button()
        minusButton.setDrawingCommands([QSize(23, 25), (_minPath, "1", btnColor)])
        minusButton.setProperty("delta", -10)
        minusButton.pressed.connect(self._sizeOffset)
        self.sizeEdit = QSpinBox(self)
        self.sizeEdit.setButtonSymbols(QSpinBox.NoButtons)
        self.sizeEdit.setFixedWidth(56)
        self.sizeEdit.setFrame(False)
        self.sizeEdit.lineEdit().setAlignment(Qt.AlignCenter)
        plusButton = Button()
        plusButton.setDrawingCommands([QSize(23, 25), (_plusPath, "1", btnColor)])
        plusButton.setProperty("delta", 10)
        plusButton.pressed.connect(self._sizeOffset)

        layout = QHBoxLayout(self)
        layout.addWidget(self.statusLabel)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(spacer)
        layout.addWidget(minusButton)
        layout.addWidget(self.sizeEdit)
        layout.addWidget(plusButton)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(0)

        self.sizeChanged = self.sizeEdit.valueChanged

    def text(self):
        return self.statusLabel.text()

    def setText(self, text):
        self.statusLabel.setText(text)

    def textVisible(self):
        return self.statusLabel.isVisible()

    def setTextVisible(self, value):
        self.statusLabel.setVisible(value)

    def minimumSize(self):
        return self.sizeEdit.minimum()

    def setMinimumSize(self, value):
        self.sizeEdit.blockSignals(True)
        self.sizeEdit.setMinimum(value)
        self.sizeEdit.blockSignals(False)

    def maximumSize(self):
        return self.sizeEdit.maximum()

    def setMaximumSize(self, value):
        self.sizeEdit.blockSignals(True)
        self.sizeEdit.setMaximum(value)
        self.sizeEdit.blockSignals(False)

    def shouldPropagateSize(self):
        return self._shouldPropagateSize

    def setShouldPropagateSize(self, value):
        self._shouldPropagateSize = value

    def unit(self):
        return self.sizeEdit.suffix()

    def setUnit(self, txt):
        self.sizeEdit.setSuffix(txt)

    def size(self):
        return self.sizeEdit.value()

    def setSize(self, value):
        value = round(value)
        self.sizeEdit.blockSignals(True)
        self.sizeEdit.setValue(value)
        self.sizeEdit.blockSignals(False)
        if self._shouldPropagateSize:
            self.sizeEdit.valueChanged.emit(value)
        # nudge label w unclamped value
        self._sliderSizeChanged(value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), Qt.white)

    def _sizeOffset(self):
        delta = self.sender().property("delta")
        cellsize = self.sizeEdit.value()
        newValue = cellsize + delta
        self.sizeEdit.setValue(newValue)

    def _sliderSizeChanged(self, value):
        self.sizeEdit.setValue(value)
