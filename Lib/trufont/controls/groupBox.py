from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QSizePolicy, QWidget)


class GroupBox(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        self.titleLabel = QLabel(self)
        self.setStyleSheet("QLabel { color: #787878 }")
        font = self.titleLabel.font()
        font.setCapitalization(QFont.AllUppercase)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        font.setPointSize(8)
        self.titleLabel.setFont(font)

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
