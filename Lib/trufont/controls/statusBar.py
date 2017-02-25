from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSpinBox, QSizePolicy, QWidget)
from trufont.objects import icons


class StatusBar(QWidget):
    """
    Use the *sizeChanged* signal for size changes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shouldPropagateSize = True

        self.statusLabel = QLabel(self)

        minusButton = QPushButton()
        minusButton.setFlat(True)
        minusButton.setIcon(icons.icon("i_minus"))
        minusButton.setProperty("delta", -10)
        minusButton.pressed.connect(self._sizeOffset)
        self.sizeEdit = QSpinBox(self)
        self.sizeEdit.setButtonSymbols(QSpinBox.NoButtons)
        self.sizeEdit.setFixedWidth(52)
        self.sizeEdit.setFrame(False)
        editor = self.sizeEdit.lineEdit()
        editor.setAlignment(Qt.AlignCenter)
        editor.setStyleSheet("color: #252525")
        plusButton = QPushButton()
        plusButton.setFlat(True)
        plusButton.setIcon(icons.icon("i_plus"))
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
        layout.setContentsMargins(21, 5, 21, 5)

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
