from defconQt.util import platformSpecific
from PyQt5.QtCore import QMimeData, QRectF, QSize, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QCursor, QDrag, QFont, QFontMetrics, QKeySequence,
    QLinearGradient, QPainter, QPen)
from PyQt5.QtWidgets import QApplication, QMessageBox, QScrollArea, QWidget
import math
import time
import unicodedata

cellGridColor = QColor(130, 130, 130)
cellHeaderBaseColor = QColor(230, 230, 230)
cellHeaderLineColor = QColor(220, 220, 220)
cellHeaderHighlightLineColor = QColor(240, 240, 240)
cellSelectionColor = QColor.fromRgbF(.2, .3, .7, .15)

GlyphCellBufferHeight = .2
GlyphCellHeaderHeight = 14

headerFont = QFont()
headerFont.setFamily('Lucida Sans Unicode')
headerFont.insertSubstitution('Lucida Sans Unicode', 'Lucida Grande')
headerFont.insertSubstitution('Lucida Sans Unicode', 'Luxi Sans')
headerFont.setPointSize(platformSpecific.headerPointSize)
voidFont = QFont(headerFont)
voidFont.setPointSize(24)
metrics = QFontMetrics(headerFont)

arrowKeys = (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right)


class GlyphCollectionWidget(QWidget):
    """
    A widget that presents a list of glyphs in cells.
    """

    def __init__(self, parent=None):
        super(GlyphCollectionWidget, self).__init__(parent)
        self.setAttribute(Qt.WA_KeyCompression)
        self._glyphs = []
        self._squareSize = 56
        self._columns = 10
        self._selection = set()
        self._oldSelection = None
        self._lastSelectedCell = None
        self._inputString = ""
        self._lastKeyInputTime = None

        self.glyphSelectedCallback = None
        self.doubleClickCallback = None
        self.updateCurrentGlyph = False
        self._maybeDragPosition = None

        self.setFocusPolicy(Qt.ClickFocus)
        self._currentDropIndex = None
        self._scrollArea = QScrollArea(parent)
        self._scrollArea.dragEnterEvent = self.pipeDragEnterEvent
        self._scrollArea.dragMoveEvent = self.pipeDragMoveEvent
        self._scrollArea.dragLeaveEvent = self.pipeDragLeaveEvent
        self._scrollArea.dropEvent = self.pipeDropEvent
        self._scrollArea.resizeEvent = self.resizeEvent
        self._scrollArea.setAcceptDrops(True)
        self._scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._scrollArea.setWidget(self)

    def proceedWithDeletion(self, erase=False):
        clear_header = self.tr("Clear glyphs")
        clear_text = self.tr("Do you want to clear selected glyphs?")
        erase_header = self.tr("Delete glyphs")
        erase_text = self.tr("Do you want to delete selected glyphs?")
        closeDialog = QMessageBox(
            QMessageBox.Question, "",
            clear_header if not erase else erase_header,
            QMessageBox.Yes | QMessageBox.No, self)
        closeDialog.setInformativeText(
            clear_text if not erase else erase_text)
        closeDialog.setModal(True)
        ret = closeDialog.exec_()
        if ret == QMessageBox.Yes:
            return True
        return False

    def _get_glyphs(self):
        return self._glyphs

    def _set_glyphs(self, glyphs):
        self._glyphs = glyphs
        self.adjustSize()
        self.selection = set()
        # self.update() # self.selection changed will do it

    glyphs = property(
        _get_glyphs, _set_glyphs, doc="A list of glyphs displayed. Clears "
        "selection and schedules display refresh when set.")

    def _get_selection(self):
        return self._selection

    def _set_selection(self, selection):
        self._selection = selection
        if not len(self._selection):
            self.lastSelectedCell = None
        self._computeGlyphSelection()
        self.update()

    selection = property(
        _get_selection, _set_selection, doc="A set that contains indexes of "
        "selected glyphs. Schedules display refresh when set.")

    def getSelectedGlyphs(self):
        return [self._glyphs[key] for key in sorted(self._selection)]

    def _get_lastSelectedCell(self):
        if self._lastSelectedCell is not None and \
                self._lastSelectedCell >= len(self._glyphs):
            return None
        return self._lastSelectedCell

    def _set_lastSelectedCell(self, index):
        self._lastSelectedCell = index
        if self.updateCurrentGlyph:
            glyph = self.lastSelectedGlyph()
            app = QApplication.instance()
            app.setCurrentGlyph(glyph)
        if index is not None:
            self.scrollToCell(index)

    lastSelectedCell = property(
        _get_lastSelectedCell, _set_lastSelectedCell,
        doc="The current lastSelectedCell in selection.")

    def lastSelectedGlyph(self):
        index = self.lastSelectedCell
        return self._glyphs[index] if index is not None else None

    def scrollArea(self):
        return self._scrollArea

    def scrollToCell(self, index):
        x = (.5 + index % self._columns) * self.squareSize
        y = (.5 + index // self._columns) * self.squareSize
        self._scrollArea.ensureVisible(
            x, y, .5 * self.squareSize, .5 * self.squareSize)

    def _get_currentDropIndex(self):
        return self._currentDropIndex

    def _set_currentDropIndex(self, index):
        self._currentDropIndex = index
        self.update()

    currentDropIndex = property(_get_currentDropIndex, _set_currentDropIndex)

    def _get_squareSize(self):
        return self._squareSize

    def _set_squareSize(self, squareSize):
        self._squareSize = squareSize
        self._rewindColumns()

    squareSize = property(_get_squareSize, _set_squareSize)

    def pipeDragEnterEvent(self, event):
        # glyph reordering
        if event.source() == self:
            event.acceptProposedAction()

    def pipeDragMoveEvent(self, event):
        # Get the position in scrollArea canvas coordinates (from the
        # beginning of the widget we are scrolling over)
        pos = self.mapFromParent(event.pos())
        self.currentDropIndex = int(
            self._columns * (pos.y() // self.squareSize) +
            (pos.x() + .5 * self.squareSize) // self.squareSize)

    def pipeDragLeaveEvent(self, event):
        self.currentDropIndex = None

    def pipeDropEvent(self, event):
        # TODO: consider dropping this check, maybe only subclasses should do
        # it so as to dispatch but here we presumably don't need it
        # TODO: shouldn't this mutate font.glyphOrder
        if event.source() == self:
            insert = self.currentDropIndex
            newGlyphNames = event.mimeData().text().split(" ")
            font = self._glyphs[0].font
            # TODO: should glyphOrder change activate font.dirty?
            newGlyphs = [font[name] for name in newGlyphNames]
            # put all glyphs to be moved to None (deleting them would
            # invalidate our insert indexes)
            for index, glyph in enumerate(self._glyphs):
                if glyph in newGlyphs:
                    self._glyphs[index] = None
            # insert newGlyphs into the list
            lst = self._glyphs[:insert]
            lst.extend(newGlyphs + self._glyphs[insert:])
            self._glyphs = lst
            # now, elide None
            self.currentDropIndex = None
            self.glyphs = [glyph
                           for glyph in self._glyphs if glyph is not None]
            # update glyphOrder
            # TODO: remove dep on parent
            font.disableNotifications("Font.GlyphOrderChanged", self.parent())
            font.glyphOrder = [glyph.name for glyph in self._glyphs]
            font.enableNotifications("Font.GlyphOrderChanged", self.parent())

    def resizeEvent(self, event):
        self._rewindColumns()

    def _rewindColumns(self):
        columns = self._scrollArea.viewport().width() // self.squareSize
        if not columns > 0:
            return
        self._columns = columns
        self.adjustSize()

    def sizeHint(self):
        # Calculate sizeHint with max(height, _scrollArea.height()) because
        # if scrollArea is bigger than widget height after an update, we risk
        # leaving old painted content on screen
        return QSize(
            self._columns * self.squareSize,
            max(math.ceil(len(self._glyphs) / self._columns) * self.squareSize,
                self._scrollArea.height()))

    # TODO: consider moving this to caller, it isn't specific to this widget
    def _computeGlyphSelection(self):
        if self.glyphSelectedCallback is None:
            return
        cnt = len(self.selection)
        if cnt == 1:
            elem = next(iter(self.selection))
            self.glyphSelectedCallback(self._glyphs[elem].name)
        else:
            self.glyphSelectedCallback(cnt)

    def _arrowKeyPressEvent(self, event):
        count = event.count()
        key = event.key()
        modifiers = event.modifiers()
        # TODO: it might be the case that self._lastSelectedCell cannot be None
        # when we arrive here whatsoever
        if self.lastSelectedCell is not None:
            if key == Qt.Key_Up:
                delta = -self._columns
            elif key == Qt.Key_Down:
                delta = self._columns
            elif key == Qt.Key_Left:
                delta = -1
            elif key == Qt.Key_Right:
                delta = 1
            newSel = self._lastSelectedCell + delta * count
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
        def isUnicodeChar(char):
            return len(char) and unicodedata.category(char) != "Cc"

        key = event.key()
        modifiers = event.modifiers()
        if key in arrowKeys:
            self._arrowKeyPressEvent(event)
        elif key == Qt.Key_Return:
            index = self.lastSelectedCell
            if index is not None and self.doubleClickCallback is not None:
                # TODO: does it still make sense to call this
                #       doubleClickCallback?
                self.doubleClickCallback(self._glyphs[index])
        elif event.matches(QKeySequence.SelectAll):
            self.selection = set(range(len(self._glyphs)))
        elif key == Qt.Key_D and modifiers & Qt.ControlModifier:
            self.selection = set()
        # XXX: this is specific to fontView so should be done thru subclassing
        # of a base widget, as is done in groupsView
        elif key == platformSpecific.deleteKey:
            erase = modifiers & Qt.ShiftModifier
            # if self.characterDeletionCallback is not None:
            if len(self._selection) and self.proceedWithDeletion(erase):
                # we need to del in reverse order to keep key references valid
                for key in sorted(self._selection, reverse=True):
                    glyph = self._glyphs[key]
                    font = glyph.font
                    if erase:
                        del font[glyph.name]
                        # Font.GlyphOrderChanged will do the update
                    else:
                        # TODO: consider putting this in glyph template setter
                        glyph.prepareUndo()
                        glyph.clear()
                        glyph.template = True
                self.selection = set()
        elif modifiers in (Qt.NoModifier, Qt.ShiftModifier) and \
                isUnicodeChar(event.text()):
            # adapted from defconAppkit
            # get the current time
            rightNow = time.time()
            # no time defined. define it.
            if self._lastKeyInputTime is None:
                self._lastKeyInputTime = rightNow
            # if the last input was too long ago,
            # clear away the old input
            if rightNow - self._lastKeyInputTime > 0.75:
                self._inputString = ""
            # reset the clock
            self._lastKeyInputTime = rightNow
            self._inputString = self._inputString + event.text()

            match = None
            matchIndex = None
            lastResort = None
            lastResortIndex = None
            for index, glyph in enumerate(self._glyphs):
                item = glyph.name
                # if the item starts with the input string, it is considered
                # a match
                if item.startswith(self._inputString):
                    if match is None:
                        match = item
                        matchIndex = index
                        continue
                    # only if the item is less than the previous match is it
                    # a more relevant match
                    # example:
                    # given this order: sys, signal
                    # and this input string: s
                    # sys will be the first match, but signal is the more
                    # accurate match
                    if item < match:
                        match = item
                        matchIndex = index
                        continue
                # if the item is greater than the input string,it can be used
                # as a last resort
                # example:
                # given this order: vanilla, zipimport
                # and this input string: x
                # zipimport will be used as the last resort
                if item > self._inputString:
                    if lastResort is None:
                        lastResort = item
                        lastResortIndex = index
                        continue
                    # if existing the last resort is greater than the item
                    # the item is a closer match to the input string
                    if lastResort > item:
                        lastResort = item
                        lastResortIndex = index
                        continue

            if matchIndex is not None:
                newSelection = matchIndex
            elif lastResortIndex is not None:
                newSelection = lastResortIndex
            if newSelection is not None:
                self.selection = {newSelection}
                self.lastSelectedCell = newSelection
        else:
            super(GlyphCollectionWidget, self).keyPressEvent(event)
            return
        event.accept()

    def _findEventIndex(self, event):
        x = max(0, min(event.x(), self.sizeHint().width() - 1))
        y = max(0, min(event.y(), self.sizeHint().height() - 1))
        index = (y // self.squareSize) * \
            self._columns + x // self.squareSize
        return index

    def _linearSelection(self, index):
        if not self._selection:
            newSelection = {index}
        else:
            if index < self.lastSelectedCell:
                newSelection = self._selection | set(
                    range(index, self.lastSelectedCell + 1))
            else:
                newSelection = self._selection | set(
                    range(self.lastSelectedCell, index + 1))
        return newSelection

    # TODO: in mousePressEvent and mouseMoveEvent below, self._lastSelectedCell
    # must be updated at all exit points
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._oldSelection = self._selection
            index = self._findEventIndex(event)
            modifiers = event.modifiers()
            event.accept()
            if index >= len(self._glyphs):
                if not (modifiers & Qt.ControlModifier or
                        modifiers & Qt.ShiftModifier):
                    self.selection = set()
                self.lastSelectedCell = index
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
                self.selection = self._linearSelection(index)
            elif index not in self._selection:
                self.selection = {index}
            else:
                self._maybeDragPosition = event.pos()
            self.lastSelectedCell = index
        else:
            super(GlyphCollectionWidget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            index = self._findEventIndex(event)
            event.accept()
            if self._maybeDragPosition is not None:
                if ((event.pos() - self._maybeDragPosition).manhattanLength()
                        < QApplication.startDragDistance()):
                        return
                # TODO: needs ordering or not?
                glyphList = " ".join(
                    glyph.name for glyph in self.getSelectedGlyphs())
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setText(glyphList)
                drag.setMimeData(mimeData)

                drag.exec_()
                self._maybeDragPosition = None
                return
            if index == self._lastSelectedCell:
                return

            modifiers = event.modifiers()
            if index >= len(self._glyphs):
                self.scrollToCell(index)
                return
            if modifiers & Qt.ControlModifier:
                if index in self._selection and index in self._oldSelection:
                    selection = self.selection
                    selection.remove(index)
                    self.selection = selection
                elif (index not in self._selection and
                      index not in self._oldSelection):
                    selection = self.selection
                    selection.add(index)
                    self.selection = selection
            elif modifiers & Qt.ShiftModifier:
                self.selection = self._linearSelection(index)
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
            if index < len(self._glyphs) and \
                    self.doubleClickCallback is not None:
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
        markGradient = QLinearGradient(
            0, 0, 0, self.squareSize - GlyphCellHeaderHeight)
        voidFont.setPointSize(.425 * self.squareSize)

        for row in range(beginRow, endRow + 1):
            for column in range(beginColumn, endColumn + 1):
                key = row * self._columns + column
                if key >= len(self._glyphs):
                    break
                glyph = self._glyphs[key]

                painter.save()
                painter.translate(column * self.squareSize,
                                  row * self.squareSize)
                painter.fillRect(0, 0, self.squareSize,
                                 self.squareSize, Qt.white)
                # prepare header colors
                brushColor = gradient
                linesColor = cellHeaderHighlightLineColor
                # mark color
                if not glyph.template and glyph.markColor is not None:
                    markColor = QColor.fromRgbF(*tuple(glyph.markColor))
                    markGradient.setColorAt(1.0, markColor)
                    markGradient.setColorAt(0.0, markColor.lighter(125))
                    painter.fillRect(0, GlyphCellHeaderHeight, self.squareSize,
                                     self.squareSize - GlyphCellHeaderHeight,
                                     QBrush(markGradient))
                if not glyph.template and glyph.dirty:
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
                painter.drawLine(self.squareSize - 2, 0,
                                 self.squareSize - 2,
                                 GlyphCellHeaderHeight - 1)
                painter.setPen(QColor(170, 170, 170))
                painter.drawLine(0, GlyphCellHeaderHeight,
                                 self.squareSize, GlyphCellHeaderHeight)
                painter.setRenderHint(QPainter.Antialiasing)
                # header text
                painter.setFont(headerFont)
                painter.setPen(QColor(80, 80, 80))
                name = metrics.elidedText(
                    glyph.name, Qt.ElideRight, self.squareSize - 2)
                painter.drawText(1, 0, self.squareSize - 2,
                                 GlyphCellHeaderHeight - minOffset,
                                 Qt.TextSingleLine | Qt.AlignCenter,
                                 name)
                painter.restore()

                painter.setPen(cellGridColor)
                rightEdgeX = column * self.squareSize + self.squareSize
                bottomEdgeY = row * self.squareSize + self.squareSize
                painter.drawLine(rightEdgeX, row *
                                 self.squareSize + 1, rightEdgeX, bottomEdgeY)
                painter.drawLine(rightEdgeX, bottomEdgeY,
                                 column * self.squareSize + 1, bottomEdgeY)
                if self._currentDropIndex is not None:
                    painter.setPen(Qt.green)
                    if self._currentDropIndex == key:
                        painter.drawLine(
                            column * self.squareSize, row * self.squareSize,
                            column * self.squareSize, bottomEdgeY)
                    # special-case the end-column
                    elif (column == endColumn and
                            self._currentDropIndex == key + 1):
                        yPos = self.mapFromGlobal(QCursor.pos()).y()
                        if row == yPos // self.squareSize:
                            painter.drawLine(
                                rightEdgeX - 1, row * self.squareSize,
                                rightEdgeX - 1, bottomEdgeY)

                # selection code
                if key in self._selection:
                    painter.setRenderHint(QPainter.Antialiasing, False)
                    painter.fillRect(column * self.squareSize + 1,
                                     row * self.squareSize + 1,
                                     self.squareSize - 3,
                                     self.squareSize - 3,
                                     cellSelectionColor)
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
                    factor = (self.squareSize - GlyphCellHeaderHeight) / \
                        (uPM * (1 + 2 * GlyphCellBufferHeight))
                    x_offset = (self.squareSize - glyph.width * factor) / 2
                    # If the glyph overflows horizontally we need to adjust the
                    # scaling factor
                    if x_offset < 0:
                        factor *= 1 + 2 * x_offset / (glyph.width * factor)
                        x_offset = 0
                    # TODO: the * 1.8 below is somewhat artificial
                    y_offset = descender * factor * 1.8
                    painter.save()
                    painter.setClipRect(
                        column * self.squareSize,
                        row * self.squareSize + GlyphCellHeaderHeight,
                        self.squareSize,
                        self.squareSize - GlyphCellHeaderHeight)
                    painter.translate(
                        column * self.squareSize + x_offset,
                        row * self.squareSize + self.squareSize + y_offset)
                    painter.scale(factor, -factor)
                    painter.fillPath(outline, Qt.black)
                    painter.restore()
                else:
                    painter.save()
                    painter.setFont(voidFont)
                    painter.setPen(QPen(Qt.lightGray))
                    rect = QRectF(
                        column * self.squareSize,
                        row * self.squareSize + GlyphCellHeaderHeight,
                        self.squareSize,
                        self.squareSize - GlyphCellHeaderHeight)
                    if glyph.unicode is not None:
                        text = chr(glyph.unicode)
                    else:
                        text = "✌"
                    painter.drawText(rect, Qt.AlignCenter, text)
                    painter.restore()
