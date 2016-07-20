from PyQt5.QtCore import pyqtSignal, QPoint, Qt
from PyQt5.QtWidgets import QLabel


class ClickLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def contextMenu(self):
        return None

    def showContextMenu(self):
        menu = self.contextMenu()
        if menu is None:
            return
        text = self.text()
        for action in menu.actions():
            if action.text() == text:
                action.setCheckable(True)
                action.setChecked(True)
        pos = QPoint(0, self.height())
        menu.exec_(self.mapToGlobal(pos))
        # leaveEvent isn't always triggered since we overlay a menu
        # cleanup manually.
        self._disableUnderline()

    def _disableUnderline(self):
        font = self.font()
        font.setUnderline(False)
        self.setFont(font)

    # ----------
    # Qt methods
    # ----------

    def enterEvent(self, event):
        font = self.font()
        font.setUnderline(True)
        self.setFont(font)

    def leaveEvent(self, event):
        self._disableUnderline()

    def mousePressEvent(self, event):
        self.showContextMenu()
        self.clicked.emit()
