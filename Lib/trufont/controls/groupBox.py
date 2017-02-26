from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QSizePolicy, QWidget)
from trufont.tools import platformSpecific


class GroupBox(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.setStyleSheet("QLabel { color: #505050 }")

        self.titleLabel = QLabel(self)
        font = self.titleLabel.font()
        font.setCapitalization(QFont.AllUppercase)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        font.setPointSize(platformSpecific.baseFontSize())
        self.titleLabel.setFont(font)
        self.titleLabel.setStyleSheet("color: #787878")

        layout = QVBoxLayout(self)
        layout.addWidget(self.titleLabel)
        layout.setContentsMargins(12, 10, 12, 16)
        layout.setSpacing(16)

    def setChildLayout(self, layout):
        layout.setContentsMargins(0, 0, 0, 0)
        self.layout().addLayout(layout)

    def title(self):
        return self.titleLabel.text()

    def setTitle(self, text):
        self.titleLabel.setText(text)

    # ----------
    # Qt methods
    # ----------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(240, 240, 240))
