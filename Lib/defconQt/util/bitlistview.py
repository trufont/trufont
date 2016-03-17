from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListView, QSizePolicy


# A QListView to display bit fields. Resizes automatically to fit all flags
# without vertical scroll bars, no horizontal scroll bars.
class BitListView(QListView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    # https://forum.qt.io/topic/40717/set-size-of-the-qlistview-to-fit-to-it-s-content/7  # noqa
    def sizeHint(self):
        hint = super().sizeHint()

        model = self.model()
        if model:
            extraHeight = self.height() - self.viewport().height()
            vRect = self.visualRect(
                model.index(model.rowCount() - 1, self.modelColumn()))
            hint.setHeight(vRect.y() + vRect.height() + extraHeight)

        return hint
