from PyQt5.QtCore import QObject


class BaseButton(QObject):
    name = "Button"
    iconPath = None

    def __init__(self, parent=None):
        super().__init__(parent)

    @property
    def _glyph(self):
        return self.parent().glyph()

    # event

    def clicked(self):
        raise NotImplementedError
