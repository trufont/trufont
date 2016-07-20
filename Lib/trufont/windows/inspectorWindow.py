from defconQt.controls.accordionBox import AccordionBox
from defconQt.controls.colorVignette import ColorVignette
from defconQt.controls.listView import ListView
from defconQt.tools.drawing import colorToQColor
from PyQt5.QtCore import QRegularExpression, Qt
from PyQt5.QtGui import (
    QColor, QIcon, QIntValidator, QDoubleValidator,
    QRegularExpressionValidator)
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QGridLayout, QLineEdit, QPushButton, QSizePolicy,
    QToolButton, QVBoxLayout, QWidget)
from trufont.controls.glyphAlignmentWidget import GlyphAlignmentWidget
from trufont.objects import settings
# TODO: switch to QFormLayout
from trufont.tools.rlabel import RLabel


class InspectorWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool)
        self.setWindowTitle(self.tr("Inspector"))
        self._font = None
        self._glyph = None

        glyphGroup = AccordionBox(self.tr("Glyph"), self)
        glyphLayout = QGridLayout(self)
        columnOneWidth = self.fontMetrics().width('0') * 7

        nameLabel = RLabel(self.tr("Name:"), self)
        self.nameEdit = QLineEdit(self)
        self.nameEdit.editingFinished.connect(self.writeGlyphName)
        unicodesLabel = RLabel(self.tr("Unicode:"), self)
        self.unicodesEdit = QLineEdit(self)
        self.unicodesEdit.editingFinished.connect(self.writeUnicodes)
        unicodesRegExp = QRegularExpression(
            "(|([a-fA-F0-9]{4,6})( ([a-fA-F0-9]{4,6}))*)")
        unicodesValidator = QRegularExpressionValidator(unicodesRegExp, self)
        self.unicodesEdit.setValidator(unicodesValidator)
        widthLabel = RLabel(self.tr("Width:"), self)
        self.widthEdit = QLineEdit(self)
        self.widthEdit.editingFinished.connect(self.writeWidth)
        self.widthEdit.setMaximumWidth(columnOneWidth)
        self.widthEdit.setValidator(QIntValidator(self))
        leftSideBearingLabel = RLabel(self.tr("Left:"), self)
        self.leftSideBearingEdit = QLineEdit(self)
        self.leftSideBearingEdit.editingFinished.connect(
            self.writeLeftSideBearing)
        self.leftSideBearingEdit.setMaximumWidth(columnOneWidth)
        self.leftSideBearingEdit.setValidator(QIntValidator(self))
        rightSideBearingLabel = RLabel(self.tr("Right:"), self)
        self.rightSideBearingEdit = QLineEdit(self)
        self.rightSideBearingEdit.editingFinished.connect(
            self.writeRightSideBearing)
        self.rightSideBearingEdit.setMaximumWidth(columnOneWidth)
        self.rightSideBearingEdit.setValidator(QIntValidator(self))
        markColorLabel = RLabel(self.tr("Flag:"), self)
        self.markColorWidget = ColorVignette(self)
        self.markColorWidget.colorChanged.connect(
            self.writeMarkColor)
        self.markColorWidget.setMaximumWidth(columnOneWidth)

        l = 0
        glyphLayout.addWidget(nameLabel, l, 0)
        glyphLayout.addWidget(self.nameEdit, l, 1, 1, 5)
        l += 1
        glyphLayout.addWidget(unicodesLabel, l, 0)
        glyphLayout.addWidget(self.unicodesEdit, l, 1, 1, 5)
        l += 1
        glyphLayout.addWidget(widthLabel, l, 0)
        glyphLayout.addWidget(self.widthEdit, l, 1)
        l += 1
        glyphLayout.addWidget(leftSideBearingLabel, l, 0)
        glyphLayout.addWidget(self.leftSideBearingEdit, l, 1)
        glyphLayout.addWidget(rightSideBearingLabel, l, 2)
        glyphLayout.addWidget(self.rightSideBearingEdit, l, 3)
        l += 1
        glyphLayout.addWidget(markColorLabel, l, 0)
        glyphLayout.addWidget(self.markColorWidget, l, 1)
        glyphGroup.setLayout(glyphLayout)

        transformGroup = AccordionBox(self.tr("Transform"), self)
        transformLayout = QGridLayout(self)

        self.alignmentWidget = GlyphAlignmentWidget(self)
        hMirrorButton = QToolButton()
        hMirrorButton.clicked.connect(self.hMirror)
        hMirrorButton.setIcon(QIcon(":swap.svg"))
        vMirrorButton = QToolButton()
        vMirrorButton.clicked.connect(self.vMirror)
        vMirrorButton.setIcon(QIcon(":swap-vertical.svg"))
        # TODO: implement
        alignVTopButton = QToolButton()
        alignVTopButton.setEnabled(False)
        alignVTopButton.setIcon(QIcon(":format-vertical-align-top.svg"))
        alignVCenterButton = QToolButton()
        alignVCenterButton.setEnabled(False)
        alignVCenterButton.setIcon(QIcon(":format-vertical-align-center.svg"))
        alignVBottomButton = QToolButton()
        alignVBottomButton.setEnabled(False)
        alignVBottomButton.setIcon(QIcon(":format-vertical-align-bottom.svg"))
        alignHLeftButton = QToolButton()
        alignHLeftButton.setEnabled(False)
        alignHLeftButton.setIcon(QIcon(":format-horizontal-align-left.svg"))
        alignHCenterButton = QToolButton()
        alignHCenterButton.setEnabled(False)
        alignHCenterButton.setIcon(
            QIcon(":format-horizontal-align-center.svg"))
        alignHRightButton = QToolButton()
        alignHRightButton.setEnabled(False)
        alignHRightButton.setIcon(QIcon(":format-horizontal-align-right.svg"))

        buttonsLayout = QGridLayout()
        l = 0
        buttonsLayout.addWidget(hMirrorButton, l, 0)
        buttonsLayout.addWidget(vMirrorButton, l, 1)
        l += 1
        buttonsLayout.addWidget(alignVTopButton, l, 0)
        buttonsLayout.addWidget(alignVCenterButton, l, 1)
        buttonsLayout.addWidget(alignVBottomButton, l, 2)
        buttonsLayout.addWidget(alignHLeftButton, l, 3)
        buttonsLayout.addWidget(alignHCenterButton, l, 4)
        buttonsLayout.addWidget(alignHRightButton, l, 5)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        buttonsLayout.addWidget(spacer, l, 7)

        # TODO: should this be implemented for partial selection?

        moveButton = QPushButton(self.tr("Move"), self)
        moveButton.clicked.connect(self.moveGlyph)
        moveXLabel = RLabel("x:", self)
        self.moveXEdit = QLineEdit("0", self)
        self.moveXEdit.setValidator(QIntValidator(self))
        moveYLabel = RLabel("y:", self)
        self.moveYEdit = QLineEdit("0", self)
        self.moveYEdit.setValidator(QIntValidator(self))
        moveXYBox = QCheckBox("x=y", self)
        moveXYBox.clicked.connect(self.lockMove)

        scaleButton = QPushButton(self.tr("Scale"), self)
        scaleButton.clicked.connect(self.scaleGlyph)
        scaleXLabel = RLabel("x:", self)
        self.scaleXEdit = QLineEdit("100", self)
        self.scaleXEdit.setValidator(QIntValidator(self))
        scaleYLabel = RLabel("y:", self)
        self.scaleYEdit = QLineEdit("100", self)
        self.scaleYEdit.setValidator(QIntValidator(self))
        scaleXYBox = QCheckBox("x=y", self)
        scaleXYBox.clicked.connect(self.lockScale)

        rotateButton = QPushButton(self.tr("Rotate"), self)
        rotateButton.clicked.connect(self.rotateGlyph)
        rotateLabel = RLabel("α:", self)
        self.rotateEdit = QLineEdit("0", self)
        self.rotateEdit.setValidator(QIntValidator(self))

        skewButton = QPushButton(self.tr("Skew"), self)
        skewButton.clicked.connect(self.skewGlyph)
        skewXLabel = RLabel("α:", self)
        self.skewXEdit = QLineEdit("0", self)
        self.skewXEdit.setValidator(QIntValidator(self))
        skewYLabel = RLabel("β:", self)
        self.skewYEdit = QLineEdit("0", self)
        self.skewYEdit.setValidator(QIntValidator(self))
        skewXYBox = QCheckBox("α=β", self)
        skewXYBox.clicked.connect(self.lockSkew)

        snapButton = QPushButton(self.tr("Snap"), self)
        snapButton.clicked.connect(self.snapGlyph)
        self.snapEdit = QLineEdit("1", self)
        self.snapEdit.setValidator(QDoubleValidator(self))

        l = 0
        transformLayout.addWidget(self.alignmentWidget, l, 0)
        transformLayout.addLayout(buttonsLayout, l, 1, 1, 5)
        l += 1
        transformLayout.addWidget(moveButton, l, 0)
        transformLayout.addWidget(moveXLabel, l, 1)
        transformLayout.addWidget(self.moveXEdit, l, 2)
        transformLayout.addWidget(moveYLabel, l, 3)
        transformLayout.addWidget(self.moveYEdit, l, 4)
        transformLayout.addWidget(moveXYBox, l, 5)
        l += 1
        transformLayout.addWidget(scaleButton, l, 0)
        transformLayout.addWidget(scaleXLabel, l, 1)
        transformLayout.addWidget(self.scaleXEdit, l, 2)
        transformLayout.addWidget(scaleYLabel, l, 3)
        transformLayout.addWidget(self.scaleYEdit, l, 4)
        transformLayout.addWidget(scaleXYBox, l, 5)
        l += 1
        transformLayout.addWidget(rotateButton, l, 0)
        transformLayout.addWidget(rotateLabel, l, 1)
        transformLayout.addWidget(self.rotateEdit, l, 2)
        l += 1
        transformLayout.addWidget(skewButton, l, 0)
        transformLayout.addWidget(skewXLabel, l, 1)
        transformLayout.addWidget(self.skewXEdit, l, 2)
        transformLayout.addWidget(skewYLabel, l, 3)
        transformLayout.addWidget(self.skewYEdit, l, 4)
        transformLayout.addWidget(skewXYBox, l, 5)
        l += 1
        transformLayout.addWidget(snapButton, l, 0)
        transformLayout.addWidget(self.snapEdit, l, 2)
        transformGroup.setLayout(transformLayout)

        layerSetGroup = AccordionBox(self.tr("Layers"), self)
        layerSetLayout = QVBoxLayout(self)

        self.layerSetView = ListView(self)
        self.layerSetView.setDragEnabled(True)
        # HACK: we need this for header labels
        self.layerSetView.setList([[None, None]])
        self.layerSetView.setHeaderLabels(
            (self.tr("Color"), self.tr("Layer Name")))
        self.layerSetView.dataDropped.connect(self.writeLayerOrder)
        self.layerSetView.valueChanged.connect(self.writeLayerAttribute)

        layerSetLayout.addWidget(self.layerSetView)
        layerSetGroup.setLayout(layerSetLayout)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(glyphGroup)
        mainLayout.addWidget(transformGroup)
        mainLayout.addWidget(layerSetGroup)
        mainLayout.addWidget(spacer)
        self.setLayout(mainLayout)

        self.readSettings()

    def readSettings(self):
        geometry = settings.inspectorWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)

    def writeSettings(self):
        settings.setInspectorWindowGeometry(self.saveGeometry())

    # -------------
    # Notifications
    # -------------

    def _unsubscribeFromGlyph(self):
        glyph = self._glyph
        if glyph is not None:
            glyph.removeObserver(self, "Glyph.Changed")

    def _subscribeToGlyph(self, glyph):
        if glyph is not None:
            glyph.addObserver(
                self, "_updateGlyphAttributes", "Glyph.Changed")

    def _unsubscribeFromFont(self):
        font = self._font
        if font is not None:
            layerSet = font.layers
            if layerSet is not None:
                layerSet.removeObserver(self, "LayerSet.Changed")

    def _subscribeToFont(self, font):
        if font is not None:
            layerSet = font.layers
            if layerSet is not None:
                layerSet.addObserver(
                    self, "_updateLayerAttributes", "LayerSet.Changed")

    def _updateGlyph(self, notification=None):
        self._unsubscribeFromGlyph()
        app = QApplication.instance()
        self._glyph = app.currentGlyph()
        self._subscribeToGlyph(self._glyph)
        self.alignmentWidget.setGlyph(self._glyph)
        self._updateGlyphAttributes()

    def _updateFont(self, notification=None):
        self._unsubscribeFromFont()
        app = QApplication.instance()
        self._font = app.currentFont()
        self._subscribeToFont(self._font)
        self._updateLayerAttributes()

    def _updateGlyphAttributes(self, notification=None):
        name = None
        unicodes = None
        width = None
        leftSideBearing = None
        rightSideBearing = None
        markColor = None
        if self._glyph is not None:
            name = self._glyph.name
            unicodes = " ".join("%06X" % u if u > 0xFFFF else "%04X" %
                                u for u in self._glyph.unicodes)
            width = str(int(self._glyph.width))
            if self._glyph.leftMargin is not None:
                leftSideBearing = str(int(self._glyph.leftMargin))
            if self._glyph.rightMargin is not None:
                rightSideBearing = str(int(self._glyph.rightMargin))
            if self._glyph.markColor is not None:
                markColor = QColor.fromRgbF(
                    *tuple(self._glyph.markColor))

        self.nameEdit.setText(name)
        self.unicodesEdit.setText(unicodes)
        self.widthEdit.setText(width)
        self.leftSideBearingEdit.setText(leftSideBearing)
        self.rightSideBearingEdit.setText(rightSideBearing)
        self.markColorWidget.setColor(markColor)

    def _updateLayerAttributes(self, notification=None):
        self.layerSetView.setList([])
        font = self._font
        if None in (font, font.layers):
            return
        layers = []
        for layer in font.layers:
            color = layer.color
            if color is not None:
                color = colorToQColor(color)
            else:
                color = QColor()
            layers.append([color, layer.name])
        self.layerSetView.setList(layers)

    # ---------
    # Callbacks
    # ---------

    # glyph attributes

    def writeGlyphName(self):
        if self._glyph is None:
            return
        # TODO: should there be an API for this (e.g. glyph.rename())
        layerSet = self._glyph.layerSet
        newName = self.nameEdit.text()
        if layerSet is not None:
            oldName = self._glyph.name
            for layer in layerSet:
                if oldName in layer:
                    glyph = layer[oldName]
                    glyph.name = newName
        else:
            self._glyph.name = newName

    def writeUnicodes(self):
        if self._glyph is None:
            return
        unicodes = self.unicodesEdit.text().split(" ")
        if len(unicodes) == 1 and unicodes[0] == "":
            self._glyph.unicodes = []
        else:
            self._glyph.unicodes = [int(uni, 16) for uni in unicodes]

    def writeWidth(self):
        if self._glyph is None:
            return
        self._glyph.width = int(self.widthEdit.text())

    def writeLeftSideBearing(self):
        if self._glyph is None:
            return
        self._glyph.leftMargin = int(self.leftSideBearingEdit.text())

    def writeRightSideBearing(self):
        if self._glyph is None:
            return
        self._glyph.rightMargin = int(self.rightSideBearingEdit.text())

    def writeMarkColor(self):
        color = self.markColorWidget.color()
        if color is not None:
            color = color.getRgbF()
        self._glyph.markColor = color

    def writeLayerAttribute(self, index, previous, current):
        font = self._font
        if None in (font, font.layers):
            return
        row, column = index.row(), index.column()
        layers = font.layers
        layer = layers[layers.layerOrder[row]]
        if column == 0:
            # color
            if current.isValid():
                color = current.getRgbF()
            else:
                color = None
            layer.color = color
        elif column == 1:
            # name
            layer.name = current
        else:
            raise ValueError("invalid column selected: %d." % column)

    def writeLayerOrder(self):
        font = self._font
        if None in (font, font.layers):
            return
        data = self.layerSetView.list()
        layerSet = font.layers
        layerOrder = []
        for _, name in data:
            layerOrder.append(name)
        # defcon has data validity assertion (constant len etc.)
        layerSet.layerOrder = layerOrder

    # transforms

    def hMirror(self):
        glyph = self._glyph
        if None in (glyph, glyph.controlPointBounds):
            return
        xMin, _, xMax, _ = glyph.controlPointBounds
        for contour in glyph:
            for point in contour:
                point.x = xMin + xMax - point.x
        glyph.dirty = True

    def vMirror(self):
        glyph = self._glyph
        if None in (glyph, glyph.controlPointBounds):
            return
        _, yMin, _, yMax = glyph.controlPointBounds
        for contour in glyph:
            for point in contour:
                point.y = yMin + yMax - point.y
        glyph.dirty = True

    def lockMove(self, checked):
        self.moveYEdit.setEnabled(not checked)

    def moveGlyph(self):
        x = self.moveXEdit.text()
        if not self.moveYEdit.isEnabled():
            y = x
        else:
            y = self.moveYEdit.text()
        x, y = int(x) if x != "" else 0, int(y) if y != "" else 0
        self._glyph.move((x, y))

    def lockScale(self, checked):
        self.scaleYEdit.setEnabled(not checked)

    def scaleGlyph(self):
        glyph = self._glyph
        # TODO: consider disabling the buttons in that case?
        if glyph is None:
            return
        sX = self.scaleXEdit.text()
        if not self.scaleYEdit.isEnabled():
            sY = sX
        else:
            sY = self.scaleYEdit.text()
        sX, sY = int(sX) if sX != "" else 100, int(sY) if sY != "" else 100
        sX /= 100
        sY /= 100
        center = self.alignmentWidget.origin()
        glyph.scale((sX, sY), center=center)

    def rotateGlyph(self):
        glyph = self._glyph
        if glyph is None:
            return
        r = self.rotateEdit.text()
        r = int(r) if r != "" else 0
        origin = self.alignmentWidget.origin()
        glyph.rotate(r, offset=origin)

    def lockSkew(self, checked):
        self.skewYEdit.setEnabled(not checked)

    def skewGlyph(self):
        glyph = self._glyph
        if glyph is None:
            return
        sX = self.skewXEdit.text()
        if not self.skewYEdit.isEnabled():
            sY = sX
        else:
            sY = self.skewYEdit.text()
        sX, sY = int(sX) if sX != "" else 0, int(sY) if sY != "" else 0
        glyph.skew((sX, sY))

    def snapGlyph(self):
        glyph = self._glyph
        if glyph is None:
            return
        base = self.snapEdit.text()
        base = float(base) if base != "" else 0
        glyph.snap(base)

    # ----------
    # Qt methods
    # ----------

    def sizeHint(self):
        sizeHint = super().sizeHint()
        sizeHint.setWidth(200)
        return sizeHint

    def showEvent(self, event):
        super().showEvent(event)
        # positioning
        # TODO: make this multiscreen aware and kick it off when restoring
        # geometry
        """
        screenRect = QApplication.desktop().availableGeometry(self)
        widgetRect = self.frameGeometry()
        x = screenRect.width() - (widgetRect.width() + 20)
        y = screenRect.center().y() - widgetRect.height() / 2
        self.move(x, y)
        """
        # notifications
        app = QApplication.instance()
        self._updateGlyph()
        app.dispatcher.addObserver(self, "_updateGlyph", "currentGlyphChanged")
        self._updateFont()
        app.dispatcher.addObserver(self, "_updateFont", "currentFontChanged")

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            app = QApplication.instance()
            app.dispatcher.removeObserver(self, "currentGlyphChanged")
            app.dispatcher.removeObserver(self, "currentFontChanged")
