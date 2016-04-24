from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication


class BaseButton(QObject):
    name = QApplication.translate("BaseButton", "Button")
    iconPath = None

    def __init__(self, parent=None):
        super().__init__(parent)

    @property
    def _glyph(self):
        return self.parent().glyph()

    # event

    def clicked(self):
        pass
