from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox


# A QCheckBox with reversed check box for better alignment of custom parameter
# layouts.
class RCheckBox(QCheckBox):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayoutDirection(Qt.RightToLeft)
