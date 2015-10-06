from PyQt5.QtCore import QMimeData, QRectF, QSize, Qt
from PyQt5.QtGui import (QBrush, QColor, QDrag, QFont, QFontMetrics, QKeySequence,
    QLinearGradient, QPainter, QPen)
from PyQt5.QtWidgets import QApplication, QMessageBox, QScrollArea, QWidget
import math

cellGridColor = QColor(130, 130, 130)
cellHeaderBaseColor = QColor(230, 230, 230)
cellHeaderLineColor = QColor(220, 220, 220)
cellHeaderHighlightLineColor = QColor(240, 240, 240)
cellSelectionColor = QColor.fromRgbF(.2, .3, .7, .15)

GlyphCellBufferHeight = .2
GlyphCellHeaderHeight = 14

# TODO: consider extracting each platform-specific thing (fonts, shortcuts) in a
# purposed folder
headerFont = QFont()
headerFont.setFamily('Lucida Sans Unicode')
headerFont.insertSubstitution('Lucida Sans Unicode', 'Lucida Grande')
headerFont.insertSubstitution('Lucida Sans Unicode', 'Luxi Sans')
headerFont.setPointSize(8)
voidFont = QFont(headerFont)
voidFont.setPointSize(24)
metrics = QFontMetrics(headerFont)

def proceedWithDeletion(self):
    closeDialog = QMessageBox(QMessageBox.Question, "", "Delete glyphs",
      QMessageBox.Yes | QMessageBox.No, self)
    closeDialog.setInformativeText("Are you sure you want to delete them?")
    closeDialog.setModal(True)
    ret = closeDialog.exec_()
    if ret == QMessageBox.Yes:
        return True
    return False

"""
A widget that presents a list of glyphs in cells.
"""
class GlyphCollectionWidget(QWidget):
    def __init__(self, parent=None):
        super(GlyphCollectionWidget, self).__init__(parent)
        self.setAttribute(Qt.WA_KeyCompression)
        self._glyphs = []
        # TODO: hide behind a façade
        self.squareSize = 56
        self._columns = 10
        self._selection = set()
        self._oldSelection = None
        self._lastSelectedCell = None

        self.characterSelectedCallback = None
        self.doubleClickCallback = None
        self.updateCurrentGlyph = False
        self._maybeDragPosition = None

        self.setFocusPolicy(Qt.ClickFocus)
        self._scrollArea = QScrollArea(parent)
        self._scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._scrollArea.setWidget(self)

    def _get_glyphs(self):
        return self._glyphs

    def _set_glyphs(self, glyphs):
        self._glyphs = glyphs
        self.adjustSize()
        self.selection = set()
        #self.update() # self.selection changed will do it

    glyphs = property(_get_glyphs, _set_glyphs, doc="A list of glyphs \
        displayed. Clears selection and schedules display refresh when set.")

    def _get_selection(self):
        return self._selection

    def _set_selection(self, selection):
        self._selection = selection
        self.computeCharacterSelected()
        self.update()

    selection = property(_get_selection, _set_selection, doc="A set that contains \
        indexes of selected glyphs. Schedules display refresh when set.")

    def getSelectedGlyphs(self):
        return [self._glyphs[key] for key in sorted(self._selection)]

    def _get_lastSelectedCell(self):
        return self._lastSelectedCell

    def _set_lastSelectedCell(self, index):
        self._lastSelectedCell = index
        if self.updateCurrentGlyph:
            glyph = self.lastSelectedGlyph()
            app = QApplication.instance()
            app.setCurrentGlyph(glyph)
        if index is not None:
            self.scrollToCell(index)

    lastSelectedCell = property(_get_lastSelectedCell, _set_lastSelectedCell,
        doc="The current lastSelectedCell in selection.")

    def lastSelectedGlyph(self):
        index = self._lastSelectedCell
        return self._glyphs[index] if index is not None else None

    def scrollArea(self):
        return self._scrollArea

    def scrollToCell(self, index):
        x = (.5 + index % self._columns) * self.squareSize
        y = (.5 + index // self._columns) * self.squareSize
        self._scrollArea.ensureVisible(x, y, .5*self.squareSize, .5*self.squareSize)

    # TODO: break this down into set width/set square
    # TODO: see whether scrollArea gets resizeEvents
    def _sizeEvent(self, width, squareSize=None):
        sw = self._scrollArea.verticalScrollBar().width() + self._scrollArea.contentsMargins().right()
        if squareSize is not None: self.squareSize = squareSize
        columns = (width - sw) // self.squareSize
        if not columns > 0: return
        self._columns = columns
        self.adjustSize()

    def sizeHint(self):
        # Calculate sizeHint with max(height, _scrollArea.height()) because if scrollArea is
        # bigger than widget height after an update, we risk leaving old painted content on screen
        return QSize(self._columns * self.squareSize,
                max(math.ceil(len(self._glyphs) / self._columns) * self.squareSize, self._scrollArea.height()))

    def computeCharacterSelected(self):
        if self.characterSelectedCallback is None:
            return
        cnt = len(self.selection)
        if cnt == 1:
            elem = next(iter(self.selection))
            self.characterSelectedCallback(self._glyphs[elem].name)
        else:
            self.characterSelectedCallback(cnt)

    def _arrowKeyPressEvent(self, event):
        count = event.count()
        key = event.key()
        modifiers = event.modifiers()
        # TODO: it might be the case that self._lastSelectedCell cannot be None
        # when we arrive here whatsoever
        if self._lastSelectedCell is not None:
            if key == Qt.Key_Up:
                delta = -self._columns
            elif key == Qt.Key_Down:
                delta = self._columns
            elif key == Qt.Key_Left:
                delta = -1
            elif key == Qt.Key_Right:
                delta = 1
            newSel = self._lastSelectedCell + delta*count
            if newSel < 0 or newSel >= len(self._glyphs):
                return
            if modifiers & Qt.ShiftModifier:
                sel = self._linearSelection(newSel)
                if sel is not None:
                    self.selection |= sel
            else:
                self.selection = {newSel}
            self.lastSelectedCell = newSel

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        if key == Qt.Key_Up or key == Qt.Key_Down or key == Qt.Key_Left \
            or key == Qt.Key_Right:
            self._arrowKeyPressEvent(event)
        elif event.matches(QKeySequence.SelectAll):
            self.selection = set(range(len(self._glyphs)))
        elif key == Qt.Key_D and modifiers & Qt.ControlModifier:
            self.selection = set()
        # XXX: this is specific to fontView so should be done thru subclassing of a base widget,
        # as is done in groupsView
        elif key == Qt.Key_Delete:
            #if self.characterDeletionCallback is not None:
            if proceedWithDeletion() and self.selection:
                # we need to del in reverse order to keep key references valid
                for key in sorted(self._selection, reverse=True):
                    glyph = self._glyphs[key]
                    font = glyph.getParent()
                    if modifiers & Qt.ShiftModifier:
                        del self.font[gName]
                        # XXX: need a del fn in property
                        del self._glyphs[key]
                    else:
                        # XXX: have template setter clear glyph content
                        glyph.template = True
                self.selection = set()
        else:
            super(GlyphCollectionWidget, self).keyPressEvent(event)
            return
        event.accept()

    def _findEventIndex(self, event):
        index = (event.y() // self.squareSize) * self._columns + event.x() // self.squareSize
        if index >= len(self._glyphs):
            return None
        return index

    def _linearSelection(self, index):
        if index in self._selection:
            newSelection = None
        if not self._selection:
            newSelection = {index}
        else:
            if index < self._lastSelectedCell:
                newSelection = self._selection | set(range(index, self._lastSelectedCell + 1))
            else:
                newSelection = self._selection | set(range(self._lastSelectedCell, index + 1))
        return newSelection

    # TODO: in mousePressEvent and mouseMoveEvent below, self._lastSelectedCell
    # must be updated at all exit point
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._oldSelection = self._selection
            index = self._findEventIndex(event)
            modifiers = event.modifiers()
            event.accept()
            if index is None:
                if not (modifiers & Qt.ControlModifier or modifiers & Qt.ShiftModifier):
                    self.selection = set()
                self._lastSelectedCell = index
                return

            if modifiers & Qt.ControlModifier:
                if index in self._selection:
                    selection = self.selection
                    selection.remove(index)
                    self.selection = selection
                else:
                    selection = self.selection
                    selection.add(index)
                    self.selection = selection
            elif modifiers & Qt.ShiftModifier:
                newSelection = self._linearSelection(index)
                if newSelection is not None:
                    self.selection = newSelection
            elif not index in self._selection:
                self.selection = {index}
            else:
                self._maybeDragPosition = event.pos()
            self.lastSelectedCell = index
        else:
            super(GlyphCollectionWidget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            index = self._findEventIndex(event)
            if self._maybeDragPosition is not None:
                if ((event.pos() - self._maybeDragPosition).manhattanLength() \
                    < QApplication.startDragDistance()): return
                # TODO: needs ordering or not?
                glyphList = " ".join(self._glyphs[i].name for i in self.selection)
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setText(glyphList)
                drag.setMimeData(mimeData)

                dropAction = drag.exec_()
                self._maybeDragPosition = None
                event.accept()
                return
            if index == self._lastSelectedCell:
                return

            modifiers = event.modifiers()
            event.accept()
            if index is None:
                if not (modifiers & Qt.ControlModifier or modifiers & Qt.ShiftModifier):
                    self.selection = set()
                self._lastSelectedCell = index
                return
            if modifiers & Qt.ControlModifier:
                if index in self._selection and index in self._oldSelection:
                    selection = self.selection
                    selection.remove(index)
                    self.selection = selection
                elif index not in self._selection and index not in self._oldSelection:
                    selection = self.selection
                    selection.add(index)
                    self.selection = selection
            elif modifiers & Qt.ShiftModifier:
                newSelection = self._linearSelection(index)
                if newSelection is not None:
                    self.selection = newSelection
            else:
                self.selection = {index}
            self.lastSelectedCell = index
        else:
            super(GlyphCollectionWidget, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
            self._maybeDragPosition = None
            self._oldSelection = None
        else:
            super(GlyphCollectionWidget, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
            index = self._findEventIndex(event)
            if self.doubleClickCallback is not None:
                self.doubleClickCallback(self._glyphs[index])
        else:
            super(GlyphCollectionWidget, self).mousePressEvent(event)

    # TODO: see if more of this process can be delegated to a factory
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        redrawRect = event.rect()
        beginRow = redrawRect.top() // self.squareSize
        endRow = redrawRect.bottom() // self.squareSize
        # XXX: do we need to maintain self._column when we have (endColumn -
        # beginColumn)?
        beginColumn = redrawRect.left() // self.squareSize
        endColumn = redrawRect.right() // self.squareSize

        gradient = QLinearGradient(0, 0, 0, GlyphCellHeaderHeight)
        gradient.setColorAt(0.0, cellHeaderBaseColor)
        gradient.setColorAt(1.0, cellHeaderLineColor)
        dirtyGradient = QLinearGradient(0, 0, 0, GlyphCellHeaderHeight)
        dirtyGradient.setColorAt(0.0, cellHeaderBaseColor.darker(125))
        dirtyGradient.setColorAt(1.0, cellHeaderLineColor.darker(125))
        markGradient = QLinearGradient(0, 0, 0, self.squareSize-GlyphCellHeaderHeight)

        for row in range(beginRow, endRow + 1):
            for column in range(beginColumn, endColumn + 1):
                key = row * self._columns + column
                if key >= len(self._glyphs): break
                glyph = self._glyphs[key]

                painter.save()
                painter.translate(column * self.squareSize, row * self.squareSize)
                painter.fillRect(0, 0, self.squareSize, self.squareSize, Qt.white)
                # prepare header colors
                brushColor = gradient
                linesColor = cellHeaderHighlightLineColor
                # mark color
                if not glyph.template:
                    # TODO: fetch via defcon dict
                    if "public.markColor" in glyph.lib:
                        colorStr = glyph.lib["public.markColor"].split(",")
                        if len(colorStr) == 4:
                            comp = []
                            for c in colorStr:
                                comp.append(float(c.strip()))
                            markColor = QColor.fromRgbF(*comp)
                            markGradient.setColorAt(1.0, markColor)
                            markGradient.setColorAt(0.0, markColor.lighter(125))
                            painter.fillRect(0, GlyphCellHeaderHeight, self.squareSize,
                                  self.squareSize - GlyphCellHeaderHeight, QBrush(markGradient))
                    if glyph.dirty:
                        brushColor = dirtyGradient
                        linesColor = cellHeaderHighlightLineColor.darker(110)

                # header gradient
                painter.fillRect(0, 0, self.squareSize, GlyphCellHeaderHeight,
                    QBrush(brushColor))
                # header lines
                painter.setPen(linesColor)
                minOffset = painter.pen().width()
                # disable antialiasing to avoid lines bleeding over background
                painter.setRenderHint(QPainter.Antialiasing, False)
                painter.drawLine(0, 0, 0, GlyphCellHeaderHeight - 1)
                painter.drawLine(self.squareSize - 2, 0, self.squareSize - 2, GlyphCellHeaderHeight -1)
                painter.setPen(QColor(170, 170, 170))
                painter.drawLine(0, GlyphCellHeaderHeight, self.squareSize, GlyphCellHeaderHeight)
                painter.setRenderHint(QPainter.Antialiasing)
                # header text
                painter.setFont(headerFont)
                painter.setPen(QColor(80, 80, 80))
                name = metrics.elidedText(glyph.name, Qt.ElideRight, self.squareSize - 2)
                painter.drawText(1, 0, self.squareSize - 2, GlyphCellHeaderHeight - minOffset,
                      Qt.TextSingleLine | Qt.AlignCenter, name)
                painter.restore()

                painter.setPen(cellGridColor)
                rightEdgeX = column * self.squareSize + self.squareSize
                bottomEdgeY = row * self.squareSize + self.squareSize
                painter.drawLine(rightEdgeX, row * self.squareSize + 1, rightEdgeX, bottomEdgeY)
                painter.drawLine(rightEdgeX, bottomEdgeY, column * self.squareSize + 1, bottomEdgeY)

                # selection code
                if key in self._selection:
                    painter.setRenderHint(QPainter.Antialiasing, False)
                    painter.fillRect(column * self.squareSize + 1,
                            row * self.squareSize + 1, self.squareSize - 3,
                            self.squareSize - 3, cellSelectionColor)
                    painter.setRenderHint(QPainter.Antialiasing)

                if not glyph.template:
                    font = glyph.getParent()
                    outline = glyph.getRepresentation("defconQt.QPainterPath")
                    uPM = font.info.unitsPerEm
                    if uPM is None or not uPM > 0:
                        uPM = 1000
                    descender = font.info.descender
                    if descender is None or not descender < 0:
                        descender = -250
                    factor = (self.squareSize-GlyphCellHeaderHeight) / (uPM*(1+2*GlyphCellBufferHeight))
                    x_offset = (self.squareSize-glyph.width*factor)/2
                    # If the glyph overflows horizontally we need to adjust the scaling factor
                    if x_offset < 0:
                        factor *= 1+2*x_offset/(glyph.width*factor)
                        x_offset = 0
                    # TODO: the * 1.8 below is somewhat artificial
                    y_offset = descender*factor * 1.8
                    painter.save()
                    painter.setClipRect(column * self.squareSize, row * self.squareSize+GlyphCellHeaderHeight,
                          self.squareSize, self.squareSize-GlyphCellHeaderHeight)
                    painter.translate(column * self.squareSize + x_offset, row * self.squareSize + self.squareSize + y_offset)
                    painter.scale(factor, -factor)
                    painter.fillPath(outline, Qt.black)
                    painter.restore()
                else:
                    painter.save()
                    painter.setFont(voidFont)
                    painter.setPen(QPen(Qt.lightGray))
                    rect = QRectF(column * self.squareSize, row * self.squareSize+GlyphCellHeaderHeight,
                          self.squareSize, self.squareSize-GlyphCellHeaderHeight)
                    # TODO: need to flag template glyphs as to whether they have unicodings or not
                    if glyph.unicode is not None:
                        text = chr(glyph.unicode)
                    else:
                        text = "✌"
                    painter.drawText(rect, Qt.AlignCenter, text)
                    painter.restore()
