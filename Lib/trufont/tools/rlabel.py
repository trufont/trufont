from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel


# A QLabel for right-aligning text to edit boxes to cut down repetition.
class RLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
