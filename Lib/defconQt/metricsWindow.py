from defconQt import icons_db  # noqa
from defconQt.glyphCollectionView import cellSelectionColor
from defconQt.glyphView import MainGlyphWindow
from defconQt.objects.defcon import TGlyph
from getpass import getuser
from PyQt5.QtCore import QEvent, QSettings, QSize, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QIcon, QIntValidator, QPainter, QPalette, QPen)
from PyQt5.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QLineEdit, QMenu,
    QPushButton, QScrollArea, QStyledItemDelegate, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QSizePolicy, QToolBar, QWidget)
import re

comboBoxItems = [
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "0123456789",
    "nn/? nono/? oo",
    "HH/? HOHO/? OO",
]

defaultPointSize = 150
glyphSelectionColor = QColor(cellSelectionColor)
glyphSelectionColor.setAlphaF(.09)

escapeRep = {
    "//": "/slash ",
    "\\n": "\u2029",
}
escapeRep = dict((re.escape(k), v) for k, v in escapeRep.items())
escapeRe = re.compile("|".join(escapeRep.keys()))


class MainMetricsWindow(QWidget):

    def __init__(self, font, string=None, pointSize=defaultPointSize,
                 parent=None):
        super().__init__(parent, Qt.Window)

        if string is None:
            try:
                string = self.tr("Hello {0}").format(getuser())
            except:
                string = self.tr("Hello World")
        # TODO: drop self.font and self.glyphs, store in the widgets only
        self.font = font
        self.glyphs = []
        self.toolbar = FontToolBar(pointSize, self)
        self.canvas = GlyphsCanvas(font, pointSize, self)
        self.table = SpaceTable(self)
        self.toolbar.comboBox.currentIndexChanged[
            str].connect(self.canvas.setPointSize)
        self.canvas.doubleClickCallback = self._glyphOpened
        self.canvas.pointSizeChangedCallback = self.toolbar.setPointSize
        self.canvas.selectionChangedCallback = self.table.setCurrentGlyph
        self.table.selectionChangedCallback = self.canvas.setSelected

        self.toolbar.textField.editTextChanged.connect(self._textChanged)
        self.toolbar.textField.setEditText(string)
        app = QApplication.instance()
        app.currentGlyphChanged.connect(self._textChanged)

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas.scrollArea())
        layout.addWidget(self.table)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.resize(600, 500)

        self.font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")

        self.setWindowTitle(font=self.font)

    def setWindowTitle(self, title=None, font=None):
        if title is None:
            title = self.tr("Metrics Window")
        if font is not None:
            title = "%s – %s %s" % (
                title, font.info.familyName, font.info.styleName)
        super().setWindowTitle(title)

    def showEvent(self, event):
        app = QApplication.instance()
        data = dict(window=self)
        app.postNotification("metricsWindowWillOpen", data)
        super().showEvent(event)
        app.postNotification("metricsWindowOpened", data)

    def closeEvent(self, event):
        app = QApplication.instance()
        data = dict(window=self)
        app.postNotification("metricsWindowWillClose", data)
        self.font.info.removeObserver(self, "Info.Changed")
        self._unsubscribeFromGlyphs()

    def _fontInfoChanged(self, notification):
        self.canvas.fetchFontMetrics()
        self.canvas.update()
        self.setWindowTitle(font=self.font)

    def _glyphChanged(self, notification):
        self.canvas.update()
        self.table.updateCells()

    def _glyphOpened(self, glyph):
        glyphViewWindow = MainGlyphWindow(glyph, self.parent())
        glyphViewWindow.show()

    def _textChanged(self):
        def fetchGlyphs(glyphNames, leftGlyphs=[], rightGlyphs=[]):
            ret = []
            for name in glyphNames:
                if name == "\u2029":
                    glyph = TGlyph()
                    glyph.unicode = 2029
                    ret.append(glyph)
                elif name in self.font:
                    ret.extend(leftGlyphs)
                    ret.append(self.font[name])
                    ret.extend(rightGlyphs)
            return ret

        # unsubscribe from the old glyphs
        self._unsubscribeFromGlyphs()
        # subscribe to the new glyphs
        left = self.textToGlyphNames(self.toolbar.leftTextField.text())
        newText = self.textToGlyphNames(self.toolbar.textField.currentText())
        right = self.textToGlyphNames(self.toolbar.rightTextField.text())
        leftGlyphs = fetchGlyphs(left)
        rightGlyphs = fetchGlyphs(right)
        finalGlyphs = fetchGlyphs(newText, leftGlyphs, rightGlyphs)
        self._subscribeToGlyphs(finalGlyphs)
        # set the records into the view
        self.canvas.setGlyphs(self.glyphs)
        self.table.setGlyphs(self.glyphs)

    # Tal Leming. Edited.
    def textToGlyphNames(self, text):
        def catchCompile():
            if compileStack[0] == "?":
                glyph = app.currentGlyph()
                if glyph is not None:
                    glyphNames.append(glyph.name)
            elif compileStack:
                glyphNames.append("".join(compileStack))

        app = QApplication.instance()
        # escape //, \n
        text = escapeRe.sub(lambda m: escapeRep[re.escape(m.group(0))], text)
        #
        glyphNames = []
        compileStack = None
        for c in text:
            # start a glyph name compile.
            if c == "/":
                # finishing a previous compile.
                if compileStack is not None:
                    # only add the compile if something has been added to the
                    # stack.
                    if compileStack:
                        glyphNames.append("".join(compileStack))
                # reset the stack.
                compileStack = []
            # adding to or ending a glyph name compile.
            elif compileStack is not None:
                # space. conclude the glyph name compile.
                if c == " ":
                    # only add the compile if something has been added to the
                    # stack.
                    catchCompile()
                    compileStack = None
                # add the character to the stack.
                else:
                    compileStack.append(c)
            # adding a character that needs to be converted to a glyph name.
            else:
                uni = ord(c)
                if uni == 0x2029:
                    glyphName = c
                else:
                    glyphName = self.font.unicodeData.glyphNameForUnicode(uni)
                glyphNames.append(glyphName)
        # catch remaining compile.
        if compileStack is not None and compileStack:
            catchCompile()
        return glyphNames

    def _subscribeToGlyphs(self, glyphs):
        self.glyphs = glyphs

        handledGlyphs = set()
        for glyph in self.glyphs:
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")

    def _unsubscribeFromGlyphs(self):
        handledGlyphs = set()
        for glyph in self.glyphs:
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.removeObserver(self, "Glyph.Changed")
        # self.glyphs = None

    def setGlyphs(self, glyphs):
        # unsubscribe from the old glyphs
        self._unsubscribeFromGlyphs()
        # subscribe to the new glyphs
        self._subscribeToGlyphs(glyphs)
        glyphNames = []
        for glyph in glyphs:
            if glyph.unicode:
                glyphNames.append(chr(glyph.unicode))
            else:
                glyphNames.append("".join(("/", glyph.name, " ")))
        self.toolbar.textField.setEditText("".join(glyphNames))
        # set the records into the view
        self.canvas.setGlyphs(self.glyphs)
        self.table.setGlyphs(self.glyphs)

pointSizes = [50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]


class FontToolBar(QToolBar):

    def __init__(self, pointSize, parent=None):
        super(FontToolBar, self).__init__(parent)
        auxiliaryWidth = self.fontMetrics().width('0') * 8
        self.leftTextField = QLineEdit(self)
        self.leftTextField.setMaximumWidth(auxiliaryWidth)
        self.textField = QComboBox(self)
        self.textField.setEditable(True)
        completer = self.textField.completer()
        completer.setCaseSensitivity(Qt.CaseSensitive)
        self.textField.setCompleter(completer)
        # XXX: had to use Maximum because Preferred did entend the widget(?)
        self.textField.setSizePolicy(QSizePolicy.Expanding,
                                     QSizePolicy.Maximum)
        items = QSettings().value("metricsWindow/comboBoxItems", comboBoxItems,
                                  str)
        self.textField.addItems(items)
        self.rightTextField = QLineEdit(self)
        self.rightTextField.setMaximumWidth(auxiliaryWidth)
        self.leftTextField.textEdited.connect(self.textField.editTextChanged)
        self.rightTextField.textEdited.connect(self.textField.editTextChanged)
        self.comboBox = QComboBox(self)
        self.comboBox.setEditable(True)
        self.comboBox.setValidator(QIntValidator(self))
        for p in pointSizes:
            self.comboBox.addItem(str(p))
        self.comboBox.setEditText(str(pointSize))

        self.configBar = QPushButton(self)
        self.configBar.setFlat(True)
        self.configBar.setIcon(QIcon(":/resources/settings.svg"))
        self.configBar.setStyleSheet("padding: 2px 0px; padding-right: 10px")
        self.toolsMenu = QMenu(self)
        showKerning = self.toolsMenu.addAction(
            self.tr("Show Kerning"), self.showKerning)
        showKerning.setCheckable(True)
        showMetrics = self.toolsMenu.addAction(
            self.tr("Show Metrics"), self.showMetrics)
        showMetrics.setCheckable(True)
        self.toolsMenu.addSeparator()
        wrapLines = self.toolsMenu.addAction(self.tr("Wrap lines"),
                                             self.wrapLines)
        wrapLines.setCheckable(True)
        wrapLines.setChecked(True)
        self.toolsMenu.addSeparator()
        verticalFlip = self.toolsMenu.addAction(
            self.tr("Vertical flip"), self.verticalFlip)
        verticalFlip.setCheckable(True)
        """
        lineHeight = QWidgetAction(self.toolsMenu)
        lineHeight.setText("Line height:")
        lineHeightSlider = QSlider(Qt.Horizontal, self)
        # QSlider works with integers so we'll just divide by 100 what comes
        # out of it
        lineHeightSlider.setMinimum(80)
        lineHeightSlider.setMaximum(160)
        lineHeightSlider.setValue(100)
        #lineHeightSlider.setContentsMargins(30, 0, 30, 0)
        lineHeightSlider.valueChanged.connect(self.lineHeight)
        lineHeight.setDefaultWidget(lineHeightSlider)
        self.toolsMenu.addAction(lineHeight)
        """

        self.configBar.setMenu(self.toolsMenu)

        self.addWidget(self.leftTextField)
        self.addWidget(self.textField)
        self.addWidget(self.rightTextField)
        self.addWidget(self.comboBox)
        self.addWidget(self.configBar)

    def showEvent(self, event):
        super(FontToolBar, self).showEvent(event)
        self.textField.setFocus(True)

    def setPointSize(self, pointSize):
        self.comboBox.blockSignals(True)
        self.comboBox.setEditText(str(pointSize))
        self.comboBox.blockSignals(False)

    def showKerning(self):
        action = self.sender()
        self.parent().canvas.setShowKerning(action.isChecked())

    def showMetrics(self):
        action = self.sender()
        self.parent().canvas.setShowMetrics(action.isChecked())

    def verticalFlip(self):
        action = self.sender()
        self.parent().canvas.setVerticalFlip(action.isChecked())

    def lineHeight(self, value):
        self.parent().canvas.setLineHeight(value / 100)

    def wrapLines(self):
        action = self.sender()
        self.parent().canvas.setWrapLines(action.isChecked())


class GlyphsCanvas(QWidget):

    def __init__(self, font, pointSize=defaultPointSize, parent=None):
        super(GlyphsCanvas, self).__init__(parent)
        self.setAttribute(Qt.WA_KeyCompression)
        # TODO: should we take focus by tabbing
        self.setFocusPolicy(Qt.ClickFocus)
        # XXX: make canvas font-agnostic as in defconAppkit and use
        # glyph.getParent() instead
        self.font = font
        self.fetchFontMetrics()
        self.glyphs = []
        self.ptSize = pointSize
        self.calculateScale()
        self.padding = 10
        self._showKerning = False
        self._showMetrics = False
        self._verticalFlip = False
        self._lineHeight = 1.1
        self._positions = None
        self._selected = None
        self.doubleClickCallback = None
        self.pointSizeChangedCallback = None
        self.selectionChangedCallback = None

        self._wrapLines = True
        self._scrollArea = QScrollArea(self.parent())
        self._scrollArea.resizeEvent = self.resizeEvent
        self._scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._scrollArea.setWidget(self)
        self.resize(581, 400)

    def scrollArea(self):
        return self._scrollArea

    def calculateScale(self):
        scale = self.ptSize / self.upm
        if scale < .01:
            scale = 0.01
        self.scale = scale

    def setShowKerning(self, showKerning):
        self._showKerning = showKerning
        self.adjustSize()
        self.update()

    def setShowMetrics(self, showMetrics):
        self._showMetrics = showMetrics
        self.update()

    def setVerticalFlip(self, verticalFlip):
        self._verticalFlip = verticalFlip
        self.update()

    def setLineHeight(self, lineHeight):
        self._lineHeight = lineHeight
        self.adjustSize()
        self.update()

    def setWrapLines(self, wrapLines):
        if self._wrapLines == wrapLines:
            return
        self._wrapLines = wrapLines
        if self._wrapLines:
            self._scrollArea.setHorizontalScrollBarPolicy(
                Qt.ScrollBarAlwaysOff)
            self._scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        else:
            self._scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self._scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.adjustSize()

    def fetchFontMetrics(self):
        self.ascender = self.font.info.ascender
        if self.ascender is None:
            self.ascender = 750
        self.descender = self.font.info.descender
        if self.descender is None:
            self.descender = -250
        self.upm = self.font.info.unitsPerEm
        if self.upm is None or not self.upm > 0:
            self.upm = 1000

    def setGlyphs(self, newGlyphs):
        self.glyphs = newGlyphs
        self._selected = None
        self.adjustSize()
        self.update()

    def setPointSize(self, pointSize):
        self.ptSize = int(pointSize)
        self.calculateScale()
        self.adjustSize()
        self.update()

    def setSelected(self, selected):
        self._selected = selected
        if self._positions is not None:
            cur_len = 0
            line = -1
            for index, li in enumerate(self._positions):
                if cur_len + len(li) > self._selected:
                    pos, width = li[self._selected - cur_len]
                    line = index
                    break
                cur_len += len(li)
            if line > -1:
                x = self.padding + pos + width / 2
                y = self.padding + (line + .5) * self.ptSize * self._lineHeight
                self._scrollArea.ensureVisible(
                    x, y, width / 2 + 20,
                    .5 * self.ptSize * self._lineHeight + 20)
        self.update()

    def _calcPaintWidthHeight(self):
        cur_width = 0
        max_width = 0
        lines = 1
        self._positions = [[]]
        for index, glyph in enumerate(self.glyphs):
            # line wrapping
            gWidth = glyph.width * self.scale
            doKern = index > 0 and self._showKerning and cur_width > 0
            if doKern:
                kern = self.lookupKerningValue(
                    self.glyphs[index - 1].name, glyph.name) * self.scale
            else:
                kern = 0
            if (self._wrapLines and cur_width + gWidth + kern +
                    2 * self.padding > self.width()) or glyph.unicode == 2029:
                self._positions.append([(0, gWidth)])
                cur_width = gWidth
                lines += 1
            else:
                self._positions[-1].append((cur_width, gWidth))
                cur_width += gWidth + kern
            max_width = max(cur_width, max_width)

        return (max_width + self.padding * 2,
                lines * self.ptSize * self._lineHeight + 2 * self.padding)

    def sizeHint(self):
        innerWidth = self._scrollArea.viewport().width()
        innerHeight = self._scrollArea.viewport().height()
        paintWidth, paintHeight = self._calcPaintWidthHeight()
        return QSize(
            max(innerWidth, paintWidth),
            max(innerHeight, paintHeight))

    def resizeEvent(self, event):
        maxHeight = max(self._scrollArea.viewport().height(), self.height())
        if self._wrapLines:
            self.resize(self._scrollArea.viewport().width(), maxHeight)
        else:
            maxWidth = max(self._scrollArea.viewport().width(), self.width())
            self.resize(maxWidth, maxHeight)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            # TODO: should it snap to predefined pointSizes?
            #       is the scaling factor okay?
            # XXX: current alg. is not reversible...
            decay = event.angleDelta().y() / 120.0
            scale = round(self.ptSize / 10)
            if scale == 0 and decay >= 0:
                scale = 1
            newPointSize = self.ptSize + int(decay) * scale
            if newPointSize <= 0:
                return

            self.setPointSize(newPointSize)
            if self.pointSizeChangedCallback is not None:
                self.pointSizeChangedCallback(newPointSize)
            event.accept()
        else:
            super(GlyphsCanvas, self).wheelEvent(event)

    # Tal Leming. Edited.
    def lookupKerningValue(self, first, second):
        kerning = self.font.kerning
        groups = self.font.groups
        # quickly check to see if the pair is in the kerning dictionary
        pair = (first, second)
        if pair in kerning:
            return kerning[pair]
        # get group names and make sure first and second are glyph names
        firstGroup = secondGroup = None
        if first.startswith("@MMK_L"):
            firstGroup = first
            first = None
        else:
            for group, groupMembers in groups.items():
                if group.startswith("@MMK_L"):
                    if first in groupMembers:
                        firstGroup = group
                        break
        if second.startswith("@MMK_R"):
            secondGroup = second
            second = None
        else:
            for group, groupMembers in groups.items():
                if group.startswith("@MMK_R"):
                    if second in groupMembers:
                        secondGroup = group
                        break
        # make an ordered list of pairs to look up
        pairs = [
            (first, second),
            (first, secondGroup),
            (firstGroup, second),
            (firstGroup, secondGroup)
        ]
        # look up the pairs and return any matches
        for pair in pairs:
            if pair in kerning:
                return kerning[pair]
        return 0

    def _arrowKeyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        if self._selected is not None:
            glyph = self.glyphs[self._selected]
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
        event.accept()

    def keyPressEvent(self, event):
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("metricsViewKeyPress", data)
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            self._arrowKeyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("metricsViewKeyRelease", data)
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # XXX: investigate, baselineShift is unused
            # if self._verticalFlip:
            #     baselineShift = -self.descender
            # else:
            #     baselineShift = self.ascender
            found = False
            line = \
                (event.y() - self.padding) // (self.ptSize * self._lineHeight)
            # XXX: Shouldnt // yield an int?
            line = int(line)
            if line >= len(self._positions):
                self._selected = None
                # XXX: find a way to DRY notification of self._selected changed
                # w ability to block notifications as well
                if self.selectionChangedCallback is not None:
                    self.selectionChangedCallback(self._selected)
                event.accept()
                self.update()
                return
            x = event.x() - self.padding
            for index, data in enumerate(self._positions[line]):
                pos, width = data
                if pos <= x and pos + width > x:
                    count = 0
                    for i in range(line):
                        count += len(self._positions[i])
                    self._selected = count + index
                    found = True
                    break
            if not found:
                self._selected = None
            if self.selectionChangedCallback is not None:
                self.selectionChangedCallback(self._selected)
            event.accept()
            self.update()
            # restore focus to ourselves, the table widget did take it when we
            # sent notification
            self.setFocus(Qt.MouseFocusReason)
        else:
            super(GlyphsCanvas, self).mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self._selected is not None:
            if self.doubleClickCallback is not None:
                self.doubleClickCallback(self.glyphs[self._selected])
        else:
            super(GlyphsCanvas, self).mouseDoubleClickEvent(event)

    def paintEvent(self, event):
        linePen = QPen(Qt.black)
        linePen.setWidth(3)
        width = self.width() / self.scale

        def paintLineMarks(painter):
            painter.save()
            painter.scale(self.scale, yDirection * self.scale)
            painter.setPen(linePen)
            painter.drawLine(0, self.ascender, width, self.ascender)
            painter.drawLine(0, 0, width, 0)
            painter.drawLine(0, self.descender, width, self.descender)
            painter.restore()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, self.width(), self.height(), Qt.white)
        if self._verticalFlip:
            baselineShift = -self.descender
            yDirection = 1
        else:
            baselineShift = self.ascender
            yDirection = -1
        painter.translate(self.padding, self.padding +
                          baselineShift * self.scale * self._lineHeight)
        # TODO: scale painter here to avoid g*scale everywhere below

        cur_width = 0
        if self._showMetrics:
            paintLineMarks(painter)
        for index, glyph in enumerate(self.glyphs):
            # line wrapping
            gWidth = glyph.width * self.scale
            doKern = index > 0 and self._showKerning and cur_width > 0
            if doKern:
                kern = self.lookupKerningValue(
                    self.glyphs[index - 1].name, glyph.name) * self.scale
            else:
                kern = 0
            if (self._wrapLines and cur_width + gWidth + kern +
                    2 * self.padding > self.width()) or glyph.unicode == 2029:
                painter.translate(-cur_width, self.ptSize * self._lineHeight)
                if self._showMetrics:
                    paintLineMarks(painter)
                cur_width = gWidth
            else:
                if doKern:
                    painter.translate(kern, 0)
                cur_width += gWidth + kern
            glyphPath = glyph.getRepresentation("defconQt.QPainterPath")
            painter.save()
            painter.scale(self.scale, yDirection * self.scale)
            if self._showMetrics:
                halfDescent = self.descender / 2
                painter.drawLine(0, 0, 0, halfDescent)
                painter.drawLine(glyph.width, 0, glyph.width, halfDescent)
            glyphSelected = index == self._selected
            if glyphSelected:
                painter.fillRect(0, self.descender, glyph.width,
                                 self.upm, glyphSelectionColor)
            painter.fillPath(glyphPath, Qt.black)
            app = QApplication.instance()
            data = dict(
                widget=self,
                painter=painter,
                selected=glyphSelected,
            )
            app.postNotification("metricsViewDraw", data)
            painter.restore()
            painter.translate(gWidth, 0)


class SpaceTableWidgetItem(QTableWidgetItem):

    def setData(self, role, value):
        if role & Qt.EditRole:
            # don't set empty data
            # XXX: maybe fetch the value from cell back to the editor
            if value == "":
                return
        super(SpaceTableWidgetItem, self).setData(role, value)


class GlyphCellItemDelegate(QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        editor = super(GlyphCellItemDelegate, self).createEditor(
            parent, option, index)
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


class SpaceTable(QTableWidget):

    def __init__(self, parent=None):
        super(SpaceTable, self).__init__(4, 1, parent)
        self.setAttribute(Qt.WA_KeyCompression)
        self.setItemDelegate(GlyphCellItemDelegate(self))
        data = [None, self.tr("Width"), self.tr("Left"), self.tr("Right")]
        # Don't grey-out disabled cells
        palette = self.palette()
        fgColor = palette.color(QPalette.Text)
        palette.setColor(QPalette.Disabled, QPalette.Text, fgColor)
        self.setPalette(palette)
        for index, title in enumerate(data):
            item = SpaceTableWidgetItem(title)
            item.setFlags(Qt.NoItemFlags)
            self.setItem(index, 0, item)
        # let's use this one column to compute the width of others
        self._cellWidth = .5 * self.columnWidth(0)
        self.setColumnWidth(0, self._cellWidth)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self._coloredColumn = None

        # always show a scrollbar to fix layout
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setSizePolicy(QSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed))
        self.glyphs = []
        self.fillGlyphs()
        self.resizeRowsToContents()
        self.currentItemChanged.connect(self._itemChanged)
        self.cellChanged.connect(self._cellEdited)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        # edit cell on single click, not double
        self.setEditTriggers(QAbstractItemView.CurrentChanged)
        self.selectionChangedCallback = None

    def setGlyphs(self, newGlyphs):
        self.glyphs = newGlyphs
        self.updateCells(False)

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
        glyph = self.glyphs[col - 1]
        if row == 1:
            glyph.width = item
        elif row == 2:
            glyph.leftMargin = item
        elif row == 3:
            glyph.rightMargin = item
        # defcon callbacks do the update

    def _itemChanged(self, current, previous):
        if current is not None:
            cur = current.column()
        if previous is not None:
            prev = previous.column()
            if current is not None and cur == prev:
                return
        self.colorColumn(current if current is None else cur)
        if self.selectionChangedCallback is not None:
            if current is not None:
                self.selectionChangedCallback(cur - 1)
            else:
                self.selectionChangedCallback(None)

    def colorColumn(self, column):
        emptyBrush = QBrush(Qt.NoBrush)
        selectionColor = QColor(235, 235, 235)
        for i in range(4):
            if self._coloredColumn is not None:
                item = self.item(i, self._coloredColumn)
                # cached column might be invalid if user input deleted it
                if item is not None:
                    item.setBackground(emptyBrush)
            if column is not None:
                self.item(i, column).setBackground(selectionColor)
        self._coloredColumn = column

    def sizeHint(self):
        # http://stackoverflow.com/a/7216486/2037879
        height = sum(self.rowHeight(k) for k in range(self.rowCount()))
        height += self.horizontalScrollBar().sizeHint().height()
        margins = self.contentsMargins()
        height += margins.top() + margins.bottom()
        return QSize(self.width(), height)

    def setCurrentGlyph(self, glyphIndex):
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

    def fillGlyphs(self):
        def glyphTableWidgetItem(content, disableCell=False):
            if isinstance(content, float):
                content = round(content)
            if content is not None:
                content = str(content)
            item = SpaceTableWidgetItem(content)
            if disableCell:
                item.setFlags(Qt.NoItemFlags)
            elif content is None:
                item.setFlags(Qt.ItemIsEnabled)
            # TODO: should fields be centered? I find left-aligned more
            # natural to read, personally...
            # item.setTextAlignment(Qt.AlignCenter)
            return item

        self._coloredColumn = None
        self.setColumnCount(len(self.glyphs) + 1)
        for index, glyph in enumerate(self.glyphs):
            # TODO: see about allowing glyph name edit here
            self.setItem(0, index + 1, glyphTableWidgetItem(glyph.name, True))
            self.setItem(1, index + 1, glyphTableWidgetItem(glyph.width))
            self.setItem(2, index + 1, glyphTableWidgetItem(glyph.leftMargin))
            self.setItem(3, index + 1, glyphTableWidgetItem(glyph.rightMargin))
            self.setColumnWidth(index + 1, self._cellWidth)

    def wheelEvent(self, event):
        # A mouse can only scroll along the y-axis. Use x-axis if we have one
        # (e.g. from touchpad), otherwise use y-axis.
        angleDelta = event.angleDelta().x() or event.angleDelta().y()
        cur = self.horizontalScrollBar().value()
        self.horizontalScrollBar().setValue(cur - angleDelta / 120)
        event.accept()
