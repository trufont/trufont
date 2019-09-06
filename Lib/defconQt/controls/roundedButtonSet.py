from PyQt5.QtCore import QRect, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath
from PyQt5.QtWidgets import QApplication, QSizePolicy, QWidget

_hPad = 10
_vPad = 6


class RoundedButtonSet(QWidget):
    clicked = pyqtSignal()
    SingleSelection = 1
    OneOrMoreSelection = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._options = []
        self._selection = set()
        self._selectionMode = RoundedButtonSet.SingleSelection

    def options(self):
        return self._options

    def setOptions(self, options, selectFirst=True):
        self._options = options
        if selectFirst and self._options:
            self._selection = {0}
        else:
            self._selection = set()
        self.update()

    def selectedOptions(self):
        return [self._options[index] for index in sorted(self._selection)]

    def setSelectedOptions(self, options):
        self._selection = set()
        for option in options:
            index = self._options.index(option)
            self._selection.add(index)
        self.update()

    def selectionMode(self):
        return self._selectionMode

    def setSelectionMode(self, mode):
        self._selectionMode = mode

    # ----------
    # Qt methods
    # ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for recordIndex, rect in self._optionsRects.items():
                if QRect(*rect).contains(event.pos()):
                    self._clickedIndex = recordIndex
                    self._oldSelection = self._selection
                    self._selection = {recordIndex}
                    if (
                        self._selectionMode > 1
                        and QApplication.keyboardModifiers() & Qt.ShiftModifier
                    ):
                        shiftSelection = self._selection ^ self._oldSelection
                        if shiftSelection:
                            self._selection = shiftSelection
                    else:
                        self._selection |= self._oldSelection
                    break
            self.update()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            clickedRect = self._optionsRects[self._clickedIndex]
            if QRect(*clickedRect).contains(event.pos()):
                self._selection = {self._clickedIndex}
                if (
                    self._selectionMode > 1
                    and QApplication.keyboardModifiers() & Qt.ShiftModifier
                ):
                    shiftSelection = self._selection ^ self._oldSelection
                    if shiftSelection:
                        self._selection = shiftSelection
                self.clicked.emit()
            else:
                self._selection = self._oldSelection
            self.update()
            del self._clickedIndex
            del self._oldSelection
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._optionsRects = {}
        w, h = self.width(), self.height()
        metrics = self.fontMetrics()
        hphp = 2 * _hPad

        painter.save()
        path = QPainterPath()
        path.addRoundedRect(0.5, 0.5, w - 1, h - 1, 4, 4)
        painter.fillPath(path, QColor(250, 250, 250))
        x = 0
        linePath = QPainterPath()
        for text in self._options[:-1]:
            x += hphp + metrics.width(text)
            linePath.moveTo(x, 0)
            linePath.lineTo(x, h)
        pen = painter.pen()
        pen.setColor(QColor(218, 218, 218))
        pen.setWidth(0)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.drawPath(linePath)
        painter.restore()

        painter.translate(_hPad, _vPad + metrics.ascent())
        left = 0
        for index, text in enumerate(self._options):
            if index in self._selection:
                color = QColor(20, 146, 230)
            else:
                color = QColor(63, 63, 63)
            painter.setPen(color)
            painter.drawText(0, 0, text)
            textWidth = metrics.width(text)
            rectWidth = textWidth + hphp
            rect = (left, 0, rectWidth, h)
            self._optionsRects[index] = rect
            painter.translate(rectWidth, 0)
            left += rectWidth

    def sizeHint(self):
        metrics = self.fontMetrics()
        hphp = 2 * _hPad
        width = sum(metrics.width(text) + hphp for text in self._options) or hphp
        height = 2 * _vPad + metrics.lineSpacing()
        return QSize(width, height)
