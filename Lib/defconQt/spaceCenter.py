from PyQt5.QtCore import QAbstractTableModel, QEvent, QSize, Qt
from PyQt5.QtGui import (QBrush, QColor, QFont, QIcon, QKeySequence, QLinearGradient, QPainter,
        QPainterPath, QPalette, QPen)
from PyQt5.QtWidgets import (QAbstractItemView, QActionGroup, QApplication, QComboBox, QGridLayout, QLabel, QLineEdit,
        QMainWindow, QMenu, QPushButton, QScrollArea, QStyledItemDelegate, QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QSizePolicy, QSpinBox, QToolBar, QWidget)

defaultPointSize = 150

class MainSpaceWindow(QWidget):
    def __init__(self, font, string=None, pointSize=defaultPointSize, parent=None):
        super(MainSpaceWindow, self).__init__(parent, Qt.Window)

        if string is None:
            from getpass import getuser
            try:
                string = getuser()
            except:
                string = "World"
            string = "Hello %s" % string
        self.font = font
        self.glyphs = []
        self._subscribeToGlyphsText(string)
        self.toolbar = FontToolBar(string, pointSize, self)
        self.scrollArea = QScrollArea(self)
        self.canvas = GlyphsCanvas(self.font, self.glyphs, self.scrollArea, pointSize, self)
        self.scrollArea.setWidget(self.canvas)
        self.table = SpaceTable(self.glyphs, self)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.scrollArea)
        layout.addWidget(self.table)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.resize(600, 500)
        self.toolbar.comboBox.currentIndexChanged[str].connect(self.canvas._pointSizeChanged)
        self.toolbar.textField.textEdited.connect(self._textChanged)
        
        self.font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")

        self.setWindowTitle("Space center – %s %s" % (self.font.info.familyName, self.font.info.styleName))

    def setupFileMenu(self):
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&Save...", self.save, QKeySequence.Save)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)
    
    def close(self):
        self.font.info.removeObserver(self, "Info.Changed")
        self._unsubscribeFromGlyphs()
        super(MainSpaceWindow, self).close()
    
    def _fontInfoChanged(self, event):
        self.canvas.update()
    
    def _glyphChanged(self, event):
        self.canvas.update()
        self.table.blockSignals(True)
        self.table.fillGlyphs()
        self.table.blockSignals(False)
    
    def _textChanged(self, newText):
        # unsubscribe from the old glyphs
        self._unsubscribeFromGlyphs()
        # subscribe to the new glyphs
        self._subscribeToGlyphsText(newText)
        # set the records into the view
        self.canvas._glyphsChanged(self.glyphs)
        self.table._glyphsChanged(self.glyphs)
    
    # Tal Leming. Edited.
    def textToGlyphNames(self, text):
        # escape //
        text = text.replace("//", "/slash ")
        #
        glyphNames = []
        compileStack = None
        for c in text:
            # start a glyph name compile.
            if c == "/":
                # finishing a previous compile.
                if compileStack is not None:
                    # only add the compile if something has been added to the stack.
                    if compileStack:
                        glyphNames.append("".join(compileStack))
                # reset the stack.
                compileStack = []
            # adding to or ending a glyph name compile.
            elif compileStack is not None:
                # space. conclude the glyph name compile.
                if c == " ":
                    # only add the compile if something has been added to the stack.
                    if compileStack:
                        glyphNames.append("".join(compileStack))
                    compileStack = None
                # add the character to the stack.
                else:
                    compileStack.append(c)
            # adding a character that needs to be converted to a glyph name.
            else:
                glyphName = self.font.unicodeData.glyphNameForUnicode(ord(c))
                glyphNames.append(glyphName)
        # catch remaining compile.
        if compileStack is not None and compileStack:
            glyphNames.append("".join(compileStack))
        return glyphNames
    
    def _subscribeToGlyphsText(self, newText):
        glyphs = []
        glyphNames = self.textToGlyphNames(newText)

        for gName in glyphNames:
            if gName not in self.font: continue
            glyphs.append(self.font[gName])
        self._subscribeToGlyphs(glyphs)
    
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
        #self.glyphs = None

    def setGlyphs(self, glyphs):
        # unsubscribe from the old glyphs
        self._unsubscribeFromGlyphs()
        # subscribe to the new glyphs
        self._subscribeToGlyphs(glyphs)
        glyphNames = []
        for glyph in glyphs:
            glyphNames.append(chr(glyph.unicode) if glyph.unicode else "".join(("/", glyph.name, " ")))
        self.toolbar.textField.setText("".join(glyphNames))
        # set the records into the view
        self.canvas._glyphsChanged(self.glyphs)
        self.table._glyphsChanged(self.glyphs)
        
    def resizeEvent(self, event):
        if self.isVisible(): self.canvas._sizeEvent(event)
        super(MainSpaceWindow, self).resizeEvent(event)

pointSizes = [50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]

class FontToolBar(QToolBar):
    def __init__(self, string, pointSize, parent=None):
        super(FontToolBar, self).__init__(parent)
        self.textField = QLineEdit(string, self)
        self.comboBox = QComboBox(self)
        self.comboBox.setEditable(True)
        for p in pointSizes:
            self.comboBox.addItem(str(p))
        self.comboBox.lineEdit().setText(str(pointSize))

        self.configBar = QPushButton(self)
        self.configBar.setFlat(True)
        self.configBar.setIcon(QIcon("resources/ic_settings_24px.svg"))
        self.configBar.setStyleSheet("padding: 2px 0px; padding-right: 10px");
        self.toolsMenu = QMenu(self)
        showKerning = self.toolsMenu.addAction("Show Kerning", self.showKerning)
        showKerning.setCheckable(True)
        self.toolsMenu.addSeparator()
        wrapLines = self.toolsMenu.addAction("Wrap lines", self.wrapLines)
        wrapLines.setCheckable(True)
        noWrapLines = self.toolsMenu.addAction("No wrap", self.noWrapLines)
        noWrapLines.setCheckable(True)
        
        wrapLinesGroup = QActionGroup(self)
        wrapLinesGroup.addAction(wrapLines)
        wrapLinesGroup.addAction(noWrapLines)
        wrapLines.setChecked(True)
        #self.toolsMenu.setActiveAction(wrapLines)
        self.configBar.setMenu(self.toolsMenu)

        self.addWidget(self.textField)
        self.addWidget(self.comboBox)
        self.addWidget(self.configBar)
    
    def showKerning(self):
        action = self.sender()
        self.parent().canvas.setShowKerning(action.isChecked())
    
    def wrapLines(self):
        self.parent().canvas.setWrapLines(True)
    
    def noWrapLines(self):
        self.parent().canvas.setWrapLines(False)

class GlyphsCanvas(QWidget):
    def __init__(self, font, glyphs, scrollArea, pointSize=defaultPointSize, parent=None):
        super(GlyphsCanvas, self).__init__(parent)

        self.font = font
        self.ascender = font.info.ascender
        if self.ascender is None: self.ascender = 750
        self.descender = font.info.descender
        if self.descender is None: self.descender = 250
        self.upm = font.info.unitsPerEm
        if self.upm is None or not self.upm > 0: self.upm = 1000
        self.glyphs = glyphs
        self.ptSize = pointSize
        self.calculateScale()
        self.padding = 10
        self._showKerning = False
        
        self._wrapLines = True
        self.scrollArea = scrollArea
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.resize(581, 400)

    def calculateScale(self):
        scale = self.ptSize / self.upm
        if scale < .01: scale = 0.01
        self.scale = scale
    
    def setShowKerning(self, showKerning):
        self._showKerning = showKerning
        self.update()
    
    def setWrapLines(self, wrapLines):
        if self._wrapLines == wrapLines: return
        self._wrapLines = wrapLines
        if self._wrapLines:
            sw = self.scrollArea.verticalScrollBar().width() + self.scrollArea.contentsMargins().right()
            self.resize(self.parent().parent().parent().width() - sw, self.height())
            self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        else:
            sh = self.scrollArea.horizontalScrollBar().height() + self.scrollArea.contentsMargins().bottom()
            self.resize(self.width(), self.parent().parent().parent().height() - sh)
            self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.update()
    
    def _pointSizeChanged(self, pointSize):
        self.ptSize = int(pointSize)
        self.calculateScale()
        self.update()
    
    def _glyphsChanged(self, newGlyphs):
        self.glyphs = newGlyphs
        self.update()
    
    def _sizeEvent(self, event):
        if self._wrapLines:
            sw = self.scrollArea.verticalScrollBar().width() + self.scrollArea.contentsMargins().right()
            self.resize(event.size().width() - sw, self.height())
        else:
            sh = self.scrollArea.horizontalScrollBar().height() + self.scrollArea.contentsMargins().bottom()
            self.resize(self.width(), event.size().height() - sh)
    
    # if we have a cell clicked in and we click on the canvas,
    # give focus to the canvas in order to quit editing
    # TODO: Focus on individual chars and show BBox + active cell (see how rf does active cells)
    # QTableWidget.scrollToItem()
    def mousePressEvent(self, event):
        self.setFocus(Qt.MouseFocusReason)
    
    def wheelEvent(self, event):
        # TODO: should it snap to predefined pointSizes? is the scaling factor okay?
        # see how rf behaves -> scaling factor grows with sz it seems
        decay = event.angleDelta().y() / 120.0
        newPointSize = self.ptSize + int(decay) * 10
        if newPointSize <= 0: return
        # TODO: send notification to parent and do all the fuss there
        self._pointSizeChanged(newPointSize)
        
        # TODO: ugh…
        comboBox = self.parent().parent().parent().toolbar.comboBox
        comboBox.blockSignals(True)
        comboBox.setEditText(str(newPointSize))
        comboBox.blockSignals(False)
        event.accept()
    
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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, self.width(), self.height(), Qt.white)
        painter.translate(self.padding, self.padding+self.ascender*self.scale)
        # TODO: scale painter here to avoid g*scale everywhere below

        cur_width = 0
        lines = 1
        for index, glyph in enumerate(self.glyphs):
            # line wrapping
            # TODO: should padding be added for the right boundary as well? I'd say no but not sure
            gWidth = glyph.width*self.scale
            doKern = index > 0 and self._showKerning and cur_width > 0
            if doKern:
                kern = self.lookupKerningValue(self.glyphs[index-1].name, glyph.name)*self.scale
            else: kern = 0
            if self._wrapLines and cur_width + gWidth + kern + self.padding > self.width():
                painter.translate(-cur_width, self.ptSize)
                cur_width = gWidth
                lines += 1
            else:
                if doKern:
                    painter.translate(kern, 0)
                cur_width += gWidth+kern
            glyphPath = glyph.getRepresentation("defconQt.QPainterPath")
            painter.save()
            painter.scale(self.scale, -self.scale)
            painter.fillPath(glyphPath, Qt.black)
            painter.restore()
            painter.translate(gWidth, 0)
        
        scrollMargins = self.scrollArea.contentsMargins()
        innerHeight = self.scrollArea.height() - scrollMargins.top() - scrollMargins.bottom()
        if not self._wrapLines:
            innerWidth = self.scrollArea.width() - scrollMargins.left() - scrollMargins.right()
            width = max(innerWidth, cur_width+self.padding*2)
        else: width = self.width()
        self.resize(width, max(innerHeight, lines*self.ptSize+2*self.padding))

class GlyphCellItemDelegate(QStyledItemDelegate):
    # TODO: implement =... lexer
    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            chg = None
            count = event.count()
            if event.key() == Qt.Key_Up:
                chg = count
            elif event.key() == Qt.Key_Down:
                chg = -count
            elif not event.key() == Qt.Key_Return:
                return False
            if chg is not None:
                modifiers = event.modifiers()
                if modifiers & Qt.AltModifier:
                    return False
                elif modifiers & Qt.ShiftModifier:
                    chg *= 10
                    if modifiers & Qt.ControlModifier:
                        chg *= 10
                try:
                    cur = int(editor.text())
                except ValueError:
                    cur = float(editor.text())
                editor.setText(str(cur+chg))
            self.commitData.emit(editor)
            editor.selectAll()
            return True
        return False

class SpaceTable(QTableWidget):
    def __init__(self, glyphs, parent=None):
        self.glyphs = glyphs
        super(SpaceTable, self).__init__(4, len(glyphs)+1, parent)
        self.setAttribute(Qt.WA_KeyCompression)
        self.setItemDelegate(GlyphCellItemDelegate(self))
        # XXX: dunno why but without updating col count
        # scrollbar reports incorrect height...
        # fillGlyphs() will change this value back
        self.setColumnCount(len(self.glyphs)+2)
        data = [None, "Width", "Left", "Right"]
        for index, item in enumerate(data):
            cell = QTableWidgetItem(item)
            # don't set ItemIsEditable
            cell.setFlags(Qt.ItemIsEnabled)
            self.setItem(index, 0, cell)
        # let's use this one column to compute the width of others
        self._cellWidth = .7*self.columnWidth(0)
        self.setColumnWidth(0, .6*self.columnWidth(0))
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        # always show a scrollbar to fix layout
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed))
        self.fillGlyphs()
        self.resizeRowsToContents()
        self.cellChanged.connect(self._cellEdited)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        # edit cell on single click, not double
        self.setEditTriggers(QAbstractItemView.CurrentChanged)
        # TODO: investigate changing cell color as in robofont
        # http://stackoverflow.com/a/13926342/2037879

    def _glyphsChanged(self, newGlyphs):
        self.glyphs = newGlyphs
        # TODO: we don't need to reallocate cells, split alloc and fill
        self.blockSignals(True)
        self.fillGlyphs()
        self.blockSignals(False)
    
    def _cellEdited(self, row, col):
        if row == 0 or col == 0: return
        item = self.item(row, col).text()
        # Glyphs that do not have outlines leave empty cells, can't convert
        # that to a scalar
        if not item: return
        try:
            item = int(item)
        except ValueError:
            item = float(item)
        # -1 because the first col contains descriptive text
        glyph = self.glyphs[col-1]
        if row == 1:
            glyph.width = item
        elif row == 2:
            glyph.leftMargin = item
        elif row == 3:
            glyph.rightMargin = item
        # defcon callbacks do the update

    def sizeHint(self):
        # http://stackoverflow.com/a/7216486/2037879
        height = sum(self.rowHeight(k) for k in range(self.rowCount()))
        height += self.horizontalScrollBar().height()
        margins = self.contentsMargins()
        height += margins.top() + margins.bottom()
        return QSize(self.width(), height)

    def fillGlyphs(self):
        def glyphTableWidgetItem(content, blockEdition=False):
            if content is not None: content = str(content)
            item = QTableWidgetItem(content)
            if content is None or blockEdition:
                # don't set ItemIsEditable
                item.setFlags(Qt.ItemIsEnabled)
            # TODO: also set alignment during edition
            # or leave it as it is now, is fine by me...
            #item.setTextAlignment(Qt.AlignCenter)
            return item

        self.setColumnCount(len(self.glyphs)+1)
        for index, glyph in enumerate(self.glyphs):
            # TODO: see about allowing glyph name edit here
            self.setItem(0, index+1, glyphTableWidgetItem(glyph.name, True))
            self.setItem(1, index+1, glyphTableWidgetItem(glyph.width))
            self.setItem(2, index+1, glyphTableWidgetItem(glyph.leftMargin))
            self.setItem(3, index+1, glyphTableWidgetItem(glyph.rightMargin))
            self.setColumnWidth(index+1, self._cellWidth)
        
    def wheelEvent(self, event):
        cur = self.horizontalScrollBar().value()
        self.horizontalScrollBar().setValue(cur - event.angleDelta().y() / 120)
        event.accept()

if __name__ == '__main__':
    import sys
# registerallfactories
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
