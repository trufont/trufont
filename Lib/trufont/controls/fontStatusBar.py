from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QLabel, QProxyStyle, QPushButton, QSlider, QStatusBar, QStyle)
from trufont.objects import icons
from trufont.tools import platformSpecific


class FontStatusBar(QStatusBar):
    """
    Use the *sizeChanged* signal for size changes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shouldPropagateSize = True
        self._unit = None

        minusButton = QPushButton()
        minusButton.setFlat(True)
        minusButton.setIcon(icons.icon("i_minus"))
        minusButton.setProperty("delta", -10)
        minusButton.pressed.connect(self._sizeOffset)
        plusButton = QPushButton()
        plusButton.setFlat(True)
        plusButton.setIcon(icons.icon("i_plus"))
        plusButton.setProperty("delta", 10)
        plusButton.pressed.connect(self._sizeOffset)
        self.sizeSlider = QSlider(Qt.Horizontal, self)
        self.sizeSlider.setFixedWidth(.9 * self.sizeSlider.width())
        self.sizeSlider.valueChanged.connect(self._sliderSizeChanged)
        self.sizeSlider.setStyle(FontSliderProxyStyle())
        self.sizeLabel = QLabel(self)
        self.selectionLabel = QLabel(self)

        self.addPermanentWidget(minusButton)
        self.addPermanentWidget(self.sizeSlider)
        self.addPermanentWidget(plusButton)
        self.addPermanentWidget(self.sizeLabel)
        self.addWidget(self.selectionLabel)
        self.setSizeGripEnabled(False)
        if platformSpecific.needsTighterMargins():
            margins = (6, -4, 9, -3)
        else:
            margins = (4, -4, 8, -3)
        self.setContentsMargins(*margins)
        self._updateLabelWidth()

        self.sizeChanged = self.sizeSlider.valueChanged

    def text(self):
        return self.selectionLabel.text()

    def setText(self, text):
        self.selectionLabel.setText(text)

    def minimumSize(self):
        return self.sizeSlider.minimum()

    def setMinimumSize(self, value):
        self.sizeSlider.blockSignals(True)
        self.sizeSlider.setMinimum(value)
        self.sizeSlider.blockSignals(False)

    def maximumSize(self):
        return self.sizeSlider.maximum()

    def setMaximumSize(self, value):
        self.sizeSlider.blockSignals(True)
        self.sizeSlider.setMaximum(value)
        self.sizeSlider.blockSignals(False)
        # self._updateLabelWidth()

    def shouldPropagateSize(self):
        return self._shouldPropagateSize

    def setShouldPropagateSize(self, value):
        self._shouldPropagateSize = value

    def unit(self):
        return self._unit

    def setUnit(self, txt):
        self._unit = txt
        self._updateLabelWidth()

    def size(self):
        return self.sizeSlider.value()

    def setSize(self, value):
        value = round(value)
        self.sizeSlider.blockSignals(True)
        self.sizeSlider.setValue(value)
        self.sizeSlider.blockSignals(False)
        if self._shouldPropagateSize:
            self.sizeSlider.valueChanged.emit(value)
        # nudge label w unclamped value
        self._sliderSizeChanged(value)

    def _updateLabelWidth(self):
        text = "0" * 5  # len(str(self.maximumSize()))
        if self._unit is not None:
            text = "{} {}".format(text, self._unit)
        self.sizeLabel.setFixedWidth(self.sizeLabel.fontMetrics().width(text))

    def _sizeOffset(self):
        delta = self.sender().property("delta")
        cellsize = self.sizeSlider.value()
        newValue = cellsize + delta
        self.sizeSlider.setValue(newValue)

    def _sliderSizeChanged(self, value):
        if self._unit is not None:
            text = "{} {}".format(value, self._unit)
        else:
            text = str(value)
        self.sizeLabel.setText(text)


class FontSliderProxyStyle(QProxyStyle):

    def drawComplexControl(self, control, option, painter, widget):
        drawGroove = drawHandle = False
        if control == QStyle.CC_Slider:
            drawGroove = option.subControls & QStyle.SC_SliderGroove
            option.subControls ^= QStyle.SC_SliderGroove
            drawHandle = option.subControls & QStyle.SC_SliderHandle
            option.subControls ^= QStyle.SC_SliderHandle
        super().drawComplexControl(control, option, painter, widget)
        thickness = self.pixelMetric(
            QStyle.PM_SliderControlThickness, option, widget)
        if drawGroove:
            groove = self.subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderGroove, widget)
            mid = thickness / 2
            x, y, w, h = groove.x(), groove.y() + mid - 1, groove.width(), 2
            painter.fillRect(x, y, w, h, QColor(128, 128, 128))
        if drawHandle:
            handle = self.subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderHandle, widget)
            targetHeight = 16
            x, y, w, h = handle.x(), handle.y(
                ), handle.width(), handle.height()
            if h > targetHeight:
                offset = round(.5 * (h - targetHeight))
                y += offset
                h -= 2 * offset
            painter.fillRect(x, y, w, h, QColor(60, 60, 60))

    def pixelMetric(self, metric, option, widget):
        if metric == QStyle.PM_SliderLength:
            return 6
        return super().pixelMetric(metric, option, widget)
