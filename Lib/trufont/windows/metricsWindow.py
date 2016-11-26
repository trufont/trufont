from defconQt.controls.glyphLineView import GlyphLineView, GlyphLineWidget
from defconQt.controls.glyphSequenceEdit import (
    GlyphSequenceComboBox, GlyphSequenceEdit)
from defconQt.windows.baseWindows import BaseWindow
from trufont.objects import settings
from trufont.objects.defcon import TGlyph
from trufont.resources import icons_db  # noqa
from trufont.windows.glyphWindow import GlyphWindow
from PyQt5.QtCore import pyqtSignal, QEvent, QSize, QSizeF, QStandardPaths, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QCursor, QIcon, QIntValidator, QPainter, QPalette)
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QMenu, QPushButton,
    QSlider, QStyledItemDelegate, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QSizePolicy, QToolBar, QToolTip, QWidgetAction)
import os
import re

pointSizes = [50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]


class MetricsWindow(BaseWindow):

    def __init__(self, font, string=None, parent=None):
        super().__init__(parent, Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        if string is None:
            try:
                import getpass
                string = getpass.getuser()
            except:
                string = self.tr("World")
            string = self.tr("Hello {0}").format(string)

        self.toolbar = MetricsToolBar(font, self)
        self.lineView = MetricsLineView(self)
        self.table = MetricsTable(self)

        self.toolbar.glyphsChanged.connect(self.lineView.setGlyphRecords)
        self.toolbar.glyphsChanged.connect(self.table.setGlyphs)
        self.toolbar.pointSizeChanged.connect(self.lineView.setPointSize)
        self.toolbar.settingsChanged.connect(self.lineView.setSettings)
        self.toolbar.settingsChanged.connect(
            lambda s: self.table.setKerningEnabled(s["showKerning"]))
        self.lineView.glyphActivated.connect(self._glyphActivated)
        self.lineView.pointSizeModified.connect(self.toolbar.setPointSize)
        self.lineView.selectionModified.connect(self.table.setCurrentGlyph)
        self.table.selectedIndexChanged.connect(self.lineView.setSelected)

        self.toolbar.setPointSize(self.lineView.pointSize())
        self.toolbar.setWrapLines(True)
        self.toolbar.setText(string)

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.lineView)
        layout.addWidget(self.table)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.font = font
        self.font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")

        self.updateWindowTitle(font=font)

        self.readSettings()

    def readSettings(self):
        geometry = settings.metricsWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)

    def writeSettings(self):
        settings.setMetricsWindowGeometry(self.saveGeometry())

    def updateWindowTitle(self, title=None, font=None):
        if title is None:
            title = self.tr("Metrics")
        if font is not None:
            title = "%s – %s %s" % (
                title, font.info.familyName, font.info.styleName)
        self.setWindowTitle(title)

    def setGlyphs(self, glyphs):
        glyphNames = []
        for glyph in glyphs:
            if glyph.unicode is not None:
                glyphNames.append(chr(glyph.unicode))
            else:
                glyphNames.append("/%s " % glyph.name)
        self.setText("".join(glyphNames))

    def setText(self, text):
        self.toolbar.setText(text)

    # -------------
    # Notifications
    # -------------

    # font

    def _fontInfoChanged(self, notification):
        self.updateWindowTitle(font=self.font)

    # widget

    def _glyphActivated(self, glyph):
        # TODO: parent should be self. make glyphWindow independent of its
        # parent
        glyphWindow = GlyphWindow(glyph, self.parent())
        glyphWindow.show()

    # ----------
    # Qt methods
    # ----------

    def sizeHint(self):
        return QSize(1150, 630)

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

    def showEvent(self, event):
        app = QApplication.instance()
        data = dict(window=self)
        app.postNotification("metricsWindowWillOpen", data)
        super().showEvent(event)
        app.postNotification("metricsWindowOpened", data)

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            app = QApplication.instance()
            data = dict(window=self)
            app.postNotification("metricsWindowWillClose", data)
            self.font.info.removeObserver(self, "Info.Changed")
            self.toolbar.closeEvent(event)
            self.lineView.closeEvent(event)


# -------------------
# Text to glyph names
# -------------------

escapeRep = {
    "//": "/slash ",
    "\\n": "\u2029",
}
escapeRep = dict((re.escape(k), v) for k, v in escapeRep.items())
escapeRe = re.compile("|".join(escapeRep.keys()))


def _cmapFunc(c, unicodeData):
    uni = ord(c)
    if uni == 0x2029:
        glyphName = c
    else:
        glyphName = unicodeData.glyphNameForUnicode(uni)
    return glyphName


def _stackCompileFunc(glyphNames, stack):
    if stack == ["?"]:
        app = QApplication.instance()
        glyph = app.currentGlyph()
        if glyph is not None:
            glyphNames.append(glyph.name)
    elif stack:
        glyphNames.append("".join(stack))


def _textEscapeFunc(text):
    return escapeRe.sub(lambda m: escapeRep[re.escape(m.group(0))], text)


def _glyphs(self):
    text = self.text()
    glyphNames = self.splitTextFunction(
        text, self._font.unicodeData, cmapFunc=_cmapFunc,
        compileFunc=_stackCompileFunc, escapeFunc=_textEscapeFunc)
    glyphs = []
    for glyphName in glyphNames:
        if glyphName == "\u2029":
            glyph = TGlyph()
            glyph.unicode = 2029
            glyphs.append(glyph)
        elif glyphName in self._font:
            glyphs.append(self._font[glyphName])
    return glyphs


class MetricsSequenceComboBox(GlyphSequenceComboBox):
    glyphs = _glyphs


class MetricsSequenceEdit(GlyphSequenceEdit):
    glyphs = _glyphs


class MetricsToolBar(QToolBar):
    """
    Emits *pointSizeChanged*.
    """
    glyphsChanged = pyqtSignal(list)
    settingsChanged = pyqtSignal(dict)

    def __init__(self, font, parent=None):
        super().__init__(parent)
        auxiliaryWidth = self.fontMetrics().width('0') * 8
        self.leftTextField = MetricsSequenceEdit(font, self)
        self.leftTextField.setMaximumWidth(auxiliaryWidth)
        self.textField = MetricsSequenceComboBox(font, self)
        # XXX: had to use Maximum because Preferred did extend the widget(?)
        self.textField.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.rightTextField = MetricsSequenceEdit(font, self)
        self.rightTextField.setMaximumWidth(auxiliaryWidth)
        self.leftTextField.textEdited.connect(self.textField.editTextChanged)
        self.rightTextField.textEdited.connect(self.textField.editTextChanged)
        self.textField.editTextChanged.connect(self._textChanged)

        self.comboBox = QComboBox(self)
        self.comboBox.setEditable(True)
        self.comboBox.setCompleter(None)
        self.comboBox.setValidator(QIntValidator(self))
        for p in pointSizes:
            self.comboBox.addItem(str(p))
        self.pointSizeChanged = self.comboBox.currentIndexChanged[str]

        self.configBar = QPushButton(self)
        self.configBar.setFlat(True)
        self.configBar.setIcon(QIcon(":settings.svg"))
        self.configBar.setStyleSheet("padding: 2px 0px; padding-right: 10px")
        self.toolsMenu = QMenu(self)
        self._showKerning = self.toolsMenu.addAction(
            self.tr("Show Kerning"), self._kerningVisibilityChanged)
        self._showKerning.setCheckable(True)
        self._showMetrics = self.toolsMenu.addAction(
            self.tr("Show Metrics"), self._controlsTriggered)
        self._showMetrics.setCheckable(True)
        self.toolsMenu.addSeparator()
        self._verticalFlip = self.toolsMenu.addAction(
            self.tr("Vertical Flip"), self._controlsTriggered)
        self._verticalFlip.setCheckable(True)
        self._wrapLines = self.toolsMenu.addAction(
            self.tr("Wrap Lines"), self._controlsTriggered)
        self._wrapLines.setCheckable(True)
        self.toolsMenu.addSeparator()
        action = self.toolsMenu.addAction(self.tr("Line Height:"))
        action.setEnabled(False)
        lineHeight = QWidgetAction(self.toolsMenu)
        self._lineHeightSlider = slider = QSlider(Qt.Horizontal, self)
        # QSlider works with integers so we'll just divide what comes out of it
        # by 100
        slider.setMinimum(80)
        slider.setMaximum(160)
        slider.setValue(110)
        slider.valueChanged.connect(self._controlsTriggered)
        slider.valueChanged.connect(self._sliderLineHeightChanged)
        lineHeight.setDefaultWidget(slider)
        self.toolsMenu.addAction(lineHeight)
        self.configBar.setMenu(self.toolsMenu)

        self.addWidget(self.leftTextField)
        self.addWidget(self.textField)
        self.addWidget(self.rightTextField)
        self.addWidget(self.comboBox)
        self.addWidget(self.configBar)

        app = QApplication.instance()
        app.dispatcher.addObserver(
            self, "_currentGlyphChanged", "currentGlyphChanged")

        self.readSettings()

    def readSettings(self):
        items = settings.metricsWindowComboBoxItems()
        self.textField.clear()
        self.textField.addItems(items)

    # -------------
    # Notifications
    # -------------

    # app

    def _currentGlyphChanged(self, notification):
        self._textChanged()

    # widget

    def _controlsTriggered(self):
        params = dict(
            lineHeight=self._lineHeightSlider.value() / 100,
            showKerning=self._showKerning.isChecked(),
            showMetrics=self._showMetrics.isChecked(),
            verticalFlip=self._verticalFlip.isChecked(),
            wrapLines=self._wrapLines.isChecked(),
        )
        self.settingsChanged.emit(params)

    def _kerningVisibilityChanged(self):
        self._controlsTriggered()
        # if showKerning was triggered, it won't apply until we pipe the glyphs
        # again. do so
        self._textChanged()

    def _sliderLineHeightChanged(self, value):
        QToolTip.showText(QCursor.pos(), str(value / 100), self)

    def _textChanged(self):
        leftGlyphs = self.leftTextField.glyphs()
        rightGlyphs = self.rightTextField.glyphs()
        glyphs = self.textField.glyphs()
        ret = []
        for glyph in glyphs:
            ret.extend(leftGlyphs + [glyph] + rightGlyphs)
        self.glyphsChanged.emit(ret)

    # --------------
    # Public methods
    # --------------

    def setPointSize(self, pointSize):
        self.comboBox.blockSignals(True)
        self.comboBox.setEditText(str(pointSize))
        self.comboBox.blockSignals(False)

    def setText(self, text, left=None, right=None):
        self.leftTextField.setText(left)
        self.rightTextField.setText(right)
        self.textField.setEditText(text)

    def setWrapLines(self, value):
        self._wrapLines.setChecked(value)
        self._controlsTriggered()

    # TODO: more methods

    # ----------
    # Qt methods
    # ----------

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            app = QApplication.instance()
            app.dispatcher.removeObserver(self, "currentGlyphChanged")

    def showEvent(self, event):
        super().showEvent(event)
        self.textField.setFocus(True)


class MetricsLineWidget(GlyphLineWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_KeyCompression)

        # inbound notification
        app = QApplication.instance()
        app.dispatcher.addObserver(self, "_needsUpdate", "metricsViewUpdate")

    def drawGlyphForeground(self, painter, glyph, rect, selected=False):
        app = QApplication.instance()
        # TODO: no scale param with self._inverseScale? or getter function as
        # in glyphView?
        data = dict(
            widget=self,
            painter=painter,
            selected=selected,
        )
        app.postNotification("metricsViewDraw", data)

    # -------------
    # Notifications
    # -------------

    def _needsUpdate(self, notification):
        self.update()

    # --------------
    # Public methods
    # --------------

    def exportToPDF(self, path=None):
        if path is None:
            desktop = QStandardPaths.standardLocations(
                QStandardPaths.DesktopLocation)
            path = os.path.join(desktop[0], "metricsWindow.pdf")

        printer = QPrinter(QPrinter.ScreenResolution)
        printer.setOutputFileName(path)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setFullPage(True)
        printer.setPaperSize(QSizeF(self.size()), QPrinter.DevicePixel)

        painter = QPainter()
        painter.begin(printer)
        painter.setRenderHint(QPainter.Antialiasing)
        if self._rightToLeft:
            self.paintRightToLeft(painter, self.geometry())
        else:
            self.paintLeftToRight(painter, self.geometry())
        painter.end()

    # ----------
    # Qt methods
    # ----------

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            app = QApplication.instance()
            app.dispatcher.removeObserver(self, "metricsViewUpdate")

    def _arrowKeyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        if self._selected is not None:
            glyph = self._glyphRecords[self._selected].glyph
            # TODO: not really DRY w other widgets
            delta = event.count()
            if modifiers & Qt.ShiftModifier:
                delta *= 10
                if modifiers & Qt.ControlModifier:
                    delta *= 10
            if key == Qt.Key_Left:
                delta = -delta
            if modifiers & Qt.AltModifier:
                if glyph.leftMargin is not None:
                    glyph.leftMargin += delta
            else:
                glyph.width += delta

    def _navKeyPressEvent(self, event):
        key = event.key()
        if self._selected is not None:
            glyphCount = len(self._glyphRecords)
            delta = event.count()
            if key == Qt.Key_Home:
                delta = -delta
            newSelected = self._selected + delta
            if newSelected < 0 or newSelected >= glyphCount:
                return
            self.setSelected(newSelected)
            self.selectionModified.emit(self._selected)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Home, Qt.Key_End):
            self._navKeyPressEvent(event)
        elif key in (Qt.Key_Left, Qt.Key_Right):
            self._arrowKeyPressEvent(event)
        else:
            super().keyPressEvent(event)
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("metricsViewKeyPress", data)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("metricsViewKeyRelease", data)


class MetricsLineView(GlyphLineView):
    glyphLineWidgetClass = MetricsLineWidget

    def exportToPDF(self, path=None):
        self._glyphLineWidget.exportToPDF(path)

    def setSettings(self, settings):
        self.setApplyKerning(settings["showKerning"])
        self.setLineHeight(settings["lineHeight"])
        self.setDrawMetrics(settings["showMetrics"])
        self.setVerticalFlip(settings["verticalFlip"])
        self.setWrapLines(settings["wrapLines"])

    def closeEvent(self, event):
        super().closeEvent(event)
        self._glyphLineWidget.closeEvent(event)


class MetricsTableItem(QTableWidgetItem):

    def setData(self, role, value):
        if role & Qt.EditRole:
            # don't set empty data
            # TODO: maybe fetch the value from cell back to the editor
            if value == "":
                return
        super().setData(role, value)


class MetricsTableItemDelegate(QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        # editor.setAlignment(Qt.AlignCenter)
        editor.setValidator(QIntValidator(self))
        return editor

    # TODO: implement =... lexer
    # TODO: Alt+left or Alt+right don't SelectAll of the new cell
    # cell by default. Implement this.
    # TODO: cycle b/w editable cell area
    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            chg = None
            count = event.count()
            key = event.key()
            if key == Qt.Key_Up:
                chg = count
            elif key == Qt.Key_Down:
                chg = -count
            elif not key == Qt.Key_Return:
                return False
            if chg is not None:
                modifiers = event.modifiers()
                if modifiers & Qt.AltModifier:
                    return False
                elif modifiers & Qt.ShiftModifier:
                    chg *= 10
                    if modifiers & Qt.ControlModifier:
                        chg *= 10
                cur = int(editor.text())
                editor.setText(str(cur + chg))
            self.commitData.emit(editor)
            editor.selectAll()
            return True
        return False


class MetricsTable(QTableWidget):
    selectedIndexChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(5, 1, parent)
        self.setAttribute(Qt.WA_KeyCompression)
        self.setItemDelegate(MetricsTableItemDelegate(self))
        data = [
            None, self.tr("Width"), self.tr("Left"), self.tr("Right"),
            self.tr("Kerning")
        ]
        # Don't grey-out disabled cells
        palette = self.palette()
        fgColor = palette.color(QPalette.Text)
        palette.setColor(QPalette.Disabled, QPalette.Text, fgColor)
        self.setPalette(palette)
        for index, title in enumerate(data):
            item = MetricsTableItem(title)
            item.setFlags(Qt.NoItemFlags)
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(index, 0, item)
        # let's use this one column to compute the width of others
        columnWidth = self.columnWidth(0)
        self._cellWidth = .5 * columnWidth
        self.setColumnWidth(0, .55 * columnWidth)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self._coloredColumn = None
        self._kerningEnabled = False

        # always show a scrollbar to fix layout
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._glyphs = []
        self.fillGlyphs()
        self.resizeRowsToContents()
        self.currentItemChanged.connect(self._itemChanged)
        self.cellChanged.connect(self._cellEdited)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        # edit cell on single click, not double
        self.setEditTriggers(QAbstractItemView.CurrentChanged)

    # -------------
    # Notifications
    # -------------

    # font

    def _glyphChanged(self, notification):
        self.updateCells()

    def _subscribeToGlyphs(self, glyphs):
        handledGlyphs = set()
        for glyph in glyphs:
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")

    def _unsubscribeFromGlyphs(self):
        handledGlyphs = set()
        for glyph in self._glyphs:
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.removeObserver(self, "Glyph.Changed")

    # widget

    def _cellEdited(self, row, col):
        if row == 0 or col == 0:
            return
        item = self.item(row, col).text()
        # Glyphs that do not have outlines leave empty cells, can't convert
        # that to a scalar
        if not item:
            return
        item = int(item)
        # -1 because the first col contains descriptive text
        glyph = self._glyphs[col - 1]
        if row == 1:
            glyph.width = item
        elif row == 2:
            glyph.leftMargin = item
        elif row == 3:
            glyph.rightMargin = item
        elif row == 4:
            prevIndex = col - 2
            if prevIndex >= 0 and glyph.font is not None:
                prevGlyph = self._glyphs[prevIndex]
                kerning = glyph.font.kerning
                kerning.write(prevGlyph, glyph, item)
        # defcon callbacks do the update

    def _itemChanged(self, current, previous):
        if current is not None:
            cur = current.column()
        if previous is not None:
            prev = previous.column()
            if current is not None and cur == prev:
                return
        self.colorColumn(None if current is None else cur)
        if current is not None:
            sel = cur - 1
        else:
            sel = None
        self.selectedIndexChanged.emit(sel)

    # --------------
    # Public methods
    # --------------

    def glyphs(self):
        return self._glyphs

    def setGlyphs(self, glyphs):
        self._unsubscribeFromGlyphs()
        self._glyphs = glyphs
        self._subscribeToGlyphs(self._glyphs)
        self.updateCells(False)

    def kerningEnabled(self):
        return self._kerningEnabled

    def setKerningEnabled(self, value):
        if value == self._kerningEnabled:
            return
        self._kerningEnabled = value
        for i in range(self.columnCount()):
            item = self.item(4, i)
            self.closePersistentEditor(item)
        self.updateCells()

    def updateCells(self, keepColor=True):
        self.blockSignals(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        coloredColumn = self._coloredColumn
        self.fillGlyphs()
        if keepColor and coloredColumn is not None and \
                coloredColumn < self.columnCount():
            self.colorColumn(coloredColumn)
        self.setEditTriggers(QAbstractItemView.CurrentChanged)
        self.blockSignals(False)

    def colorColumn(self, column):
        emptyBrush = QBrush(Qt.NoBrush)
        selectionColor = QColor(235, 235, 235)
        for i in range(self.rowCount()):
            if self._coloredColumn is not None:
                item = self.item(i, self._coloredColumn)
                # cached column might be invalid if user input deleted it
                if item is not None:
                    item.setBackground(emptyBrush)
            if column is not None:
                self.item(i, column).setBackground(selectionColor)
        self._coloredColumn = column

    def setCurrentGlyph(self, glyphIndex):
        # disable the widget to avoid stealing focus
        self.setEnabled(False)
        self.blockSignals(True)
        if glyphIndex is not None:
            # so we can scroll to the item
            self.setCurrentCell(1, glyphIndex + 1)
        self.setCurrentItem(None)
        if glyphIndex is not None:
            self.colorColumn(glyphIndex + 1)
        else:
            self.colorColumn(glyphIndex)
        self.blockSignals(False)
        self.setEnabled(True)

    def fillGlyphs(self):
        def metricsTableItem(content, disableCell=False):
            if isinstance(content, float):
                content = round(content)
            if content is not None:
                content = str(content)
            item = MetricsTableItem(content)
            if disableCell:
                item.setFlags(Qt.NoItemFlags)
            elif content is None:
                item.setFlags(Qt.ItemIsEnabled)
            # TODO: should fields be centered? I find left-aligned more
            # natural to read, personally...
            # item.setTextAlignment(Qt.AlignCenter)
            return item

        def getKern(previousGlyph, glyph):
            if previousGlyph is None:
                return ""
            font = glyph.font
            if font is None:
                return 0
            kerning = font.kerning
            if kerning is None:
                return 0
            return kerning.find(previousGlyph, glyph)

        self._coloredColumn = None
        self.setColumnCount(len(self._glyphs) + 1)
        prevGlyph = None
        for index, glyph in enumerate(self._glyphs):
            # TODO: see about allowing glyph name edit here
            self.setItem(0, index + 1, metricsTableItem(glyph.name, True))
            self.setItem(1, index + 1, metricsTableItem(glyph.width))
            self.setItem(2, index + 1, metricsTableItem(glyph.leftMargin))
            self.setItem(3, index + 1, metricsTableItem(glyph.rightMargin))
            kValue = getKern(prevGlyph, glyph)
            kDisabled = not (index and self._kerningEnabled)
            # TODO: grey out cells when disabled
            self.setItem(4, index + 1, metricsTableItem(kValue, kDisabled))
            self.setColumnWidth(index + 1, self._cellWidth)
            prevGlyph = glyph

    # ----------
    # Qt methods
    # ----------

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self._unsubscribeFromGlyphs()

    def sizeHint(self):
        # http://stackoverflow.com/a/7216486/2037879
        height = sum(self.rowHeight(k) for k in range(self.rowCount()))
        height += self.horizontalScrollBar().height()
        margins = self.contentsMargins()
        height += margins.top() + margins.bottom()
        return QSize(self.width(), height)

    def wheelEvent(self, event):
        # A mouse can only scroll along the y-axis. Use x-axis if we have one
        # (e.g. from touchpad), otherwise use y-axis.
        angleDelta = event.angleDelta().x() or event.angleDelta().y()
        cur = self.horizontalScrollBar().value()
        self.horizontalScrollBar().setValue(cur - angleDelta / 120)
        event.accept()
