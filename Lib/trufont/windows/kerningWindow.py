from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QSize, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTreeView, QVBoxLayout, QWidget

from trufont.objects import settings


class KerningDictModel(QAbstractItemModel):
    def __init__(self, mapping={}, parent=None):
        super().__init__(parent)
        self.setupModelData(mapping)

    def setupModelData(self, mapping):
        self.layoutAboutToBeChanged.emit()
        self._data = kerns = dict()
        for key, value in mapping.items():
            kern1, kern2 = key
            kern1 = kern1.replace("public.kern1.", "@")
            kern2 = kern2.replace("public.kern2.", "@")
            ct = (kern2, value)
            if kern1 in kerns:
                kerns[kern1].append(ct)
            else:
                kerns[kern1] = [ct]
        self._keys = list(self._data.keys())
        self.layoutChanged.emit()

    def columnCount(self, parent):
        return 2

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            key = index.internalPointer()
            if key is None:
                if index.column() > 0:
                    return None
                return self._keys[index.row()]
            return self._data[key][index.row()][index.column()]
        elif role == Qt.ForegroundRole:
            data = index.data()
            if isinstance(data, str) and data.startswith("@"):
                return QColor(5, 5, 96)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if parent.isValid():
            key = self._keys[parent.row()]
            return self.createIndex(row, column, key)
        return self.createIndex(row, column, None)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        key = index.internalPointer()
        if key is None:
            return QModelIndex()
        row = self._keys.index(key)
        return self.createIndex(row, 0, None)

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self._data)
        key = parent.internalPointer()
        if key is not None:
            # child item
            return 0
        key = self._keys[parent.row()]
        return len(self._data[key])


class KerningWindow(QWidget):
    def __init__(self, font, parent=None):
        super().__init__(parent, Qt.Window)
        self._font = font
        self._font.kerning.addObserver(self, "_kerningChanged", "Kerning.Changed")
        self._font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")
        self.kerningView = QTreeView(self)
        self.kerningView.setModel(KerningDictModel(font.kerning, self.kerningView))
        self.kerningView.expandAll()
        metrics = self.kerningView.fontMetrics()
        self.kerningView.setColumnWidth(1, 8 * metrics.width("0"))
        hdr = self.kerningView.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, hdr.Stretch)
        hdr.hide()

        layout = QVBoxLayout(self)
        layout.addWidget(self.kerningView)
        layout.setContentsMargins(0, 0, 0, 0)

        self.updateWindowTitle(font=font)
        self.readSettings()

    def readSettings(self):
        geometry = settings.kerningWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)

    def writeSettings(self):
        settings.setKerningWindowGeometry(self.saveGeometry())

    def updateWindowTitle(self, title=None, font=None):
        if title is None:
            title = self.tr("Kerning")
        if font is not None:
            title = "{} – {} {}".format(
                title, font.info.familyName, font.info.styleName
            )
        self.setWindowTitle(title)

    # -------------
    # Notifications
    # -------------

    def _kerningChanged(self, notification):
        model = self.kerningView.model()
        model.setupModelData(self._font.kerning)

    def _fontInfoChanged(self, notification):
        self.updateWindowTitle(font=self._font)

    # ----------
    # Qt methods
    # ----------

    def sizeHint(self):
        return QSize(280, 460)

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self._font.kerning.removeObserver(self, "Kerning.Changed")
            self._font.info.removeObserver(self, "Info.Changed")
