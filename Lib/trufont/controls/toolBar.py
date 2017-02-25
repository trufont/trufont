from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QColor, QKeySequence, QPainter
from PyQt5.QtWidgets import QAbstractButton, QSizePolicy, QVBoxLayout, QWidget


class PathButton(QAbstractButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(90, 90, 90)
        self._path = None
        self._size = QSize(24, 24)

    def color(self):
        return self._color

    def setColor(self, color):
        self._color = color
        self.update()

    def path(self):
        return self._path

    def setPath(self, path):
        self._path = path
        self.update()

    def size(self):
        return self._size

    def setSize(self, size):
        self._size = size
        self.adjustSize()

    # ----------
    # Qt methods
    # ----------

    def paintEvent(self, event):
        if self._path is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        size = QSize(28, 28)  # self._size  XXX
        target = event.rect().size()
        if not size.isNull() and (size.width(
                ) > target.width() or size.height() > target.height()):
            sz = size.scaled(target, Qt.KeepAspectRatio)
            width, height = sz.width(
                ) / size.width(), sz.height() / size.height()
            painter.scale(width, height)
        painter.translate(0, target.height())
        painter.scale(1, -1)
        painter.fillPath(self._path, self._color)

    def sizeHint(self):
        return self._size


class ToolBar(QWidget):
    """
    TODO: allow all orientations
    """
    currentToolChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(90, 90, 90)
        self._selectedColor = QColor(31, 143, 230)
        self._currentTool = 0
        self._tools = []

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(12)

    def _buttonClicked(self):
        layout = self.layout()
        sender = self.sender()
        toolIndex = 0
        for i in range(layout.count() - 1):
            btn = layout.itemAt(i).widget()
            if btn == sender:
                color = self._selectedColor
                toolIndex = i
            else:
                color = self._color
            btn.setColor(color)
        self._currentTool = toolIndex
        self.currentToolChanged.emit(self._tools[toolIndex])

    def _updateColors(self):
        layout = self.layout()
        for i in range(layout.count() - 1):
            btn = layout.itemAt(i).widget()
            if self._currentTool == i:
                color = self._selectedColor
            else:
                color = self._color
            btn.setColor(color)

    def _updateTools(self):
        layout = self.layout()
        for i in range(layout.count(), 0, -1):
            layout.takeAt(i)
        for index, tool in enumerate(self._tools):
            btn = PathButton(self)
            if index == self._currentTool:
                color = self._selectedColor
            else:
                color = self._color
            btn.setColor(color)
            btn.setPath(tool.icon)
            text = tool.name
            if tool.shortcut is not None:
                text = "{} ({})".format(text, tool.shortcut)
                btn.setShortcut(QKeySequence(tool.shortcut))
            btn.setToolTip(text)
            btn.clicked.connect(self._buttonClicked)
            # btn.pressed.connect(lambda: btn.setColor(self._selectedColor))
            layout.addWidget(btn)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(spacer)

    def color(self):
        return self._color

    def setColor(self, color):
        self._color = color
        self._updateColors()

    def selectedColor(self):
        return self._color

    def setSelectedColor(self, color):
        self._selectedColor = color
        self._updateColors()

    def tools(self):
        return self._tools

    def setTools(self, tools):
        self._tools = list(tools)
        self._updateTools()

    def addTool(self, tool):
        self._tools.append(tool)
        self._updateTools()

    def removeTool(self, tool):
        self._tools.remove(tool)
        self._updateTools()

    def currentTool(self):
        return self._tools[self._currentTool]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(240, 240, 240))
