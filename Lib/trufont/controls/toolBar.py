from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtGui import QColor, QKeySequence, QPainter
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from trufont.controls.pathButton import PathButton


class ToolBar(QWidget):
    """
    TODO: allow all orientations
    """

    currentToolChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(90, 90, 90)
        self._selectedColor = QColor(20, 146, 230)
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
            cmds = btn.drawingCommands()
            cmds[1][2] = color
            btn.setDrawingCommands(cmds)
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
            cmds = btn.drawingCommands()
            cmds[1][2] = color
            btn.setDrawingCommands(cmds)

    def _updateTools(self):
        layout = self.layout()
        for i in reversed(range(layout.count())):
            layout.takeAt(i).widget().close()
        for index, tool in enumerate(self._tools):
            btn = PathButton(self)
            if index == self._currentTool:
                color = self._selectedColor
            else:
                color = self._color
            btn.setDrawingCommands([QSize(28, 28), [tool.icon, "f", color]])
            btn.setIsDownColor(QColor())
            btn.setIsFlipped(True)
            text = tool.name
            if tool.shortcut is not None:
                text = f"{text} ({tool.shortcut})"
                btn.setShortcut(QKeySequence(tool.shortcut))
            btn.setToolTip(text)
            btn.clicked.connect(self._buttonClicked)
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

    def setCurrentTool(self, tool):
        self._currentTool = self._tools.index(tool)
        self._updateColors()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(240, 240, 240))
