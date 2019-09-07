"""
The *glyphCellView* submodule
-----------------------------

The *glyphCellView* submodule provides a widget that displays a list of Glyph_
in cells with their names drawn inside headers.

.. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
"""

import time
import unicodedata

from defcon import Glyph
from PyQt5.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QDrag, QPainter, QPainterPath, QPalette
from PyQt5.QtWidgets import QApplication, QScrollArea, QSizePolicy, QWidget

from defconQt.representationFactories.glyphCellFactory import (
    GlyphCellHeaderHeight,
    GlyphCellMinHeightForHeader,
)
from defconQt.tools import platformSpecific
from defconQt.tools.glyphsMimeData import GlyphsMimeData

backgroundColor = Qt.white
cellGridColor = QColor(190, 190, 190)
insertionPositionColor = QColor.fromRgbF(0.16, 0.3, 0.85, 1)

cacheBustSize = 10


class GlyphCellWidget(QWidget):
    """
    The :class:`GlyphCellWidget` widget displays a list of Glyph_ organized
    in cells with their names inside headers.

    This widget allows keyboard navigation and selection of one or more cells,
    and emits the *glyphActivated* signal upon double-click or Return keyboard
    pressed and yields the concerned Glyph_.
    It also has a *selectionChanged* signal.

    Drag and drop can be enabled with *setAcceptDrops(True)*. This widget
    then supports reordering its glyph cells (in which case it emits
    *orderChanged*).

    # TODO: navigation with Shift is perfectible

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """

    glyphActivated = pyqtSignal(Glyph)
    glyphsDropped = pyqtSignal()
    selectionChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_KeyCompression)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self._cellWidth = 50
        self._cellHeight = 50
        self._cellWidthExtra = 0
        self._cellSizeCache = set()
        self._glyphs = []

        self._inputString = ""
        self._lastKeyInputTime = None
        self._selection = set()
        self._lastSelectedCell = None

        self._currentDropIndex = None
        self._maybeDragPosition = None

        self._columnCount = 0
        self._rowCount = 0

        self._cellRepresentationName = "defconQt.GlyphCell"
        self._cellRepresentationArguments = {}

    # --------------
    # Custom methods
    # --------------

    def scrollArea(self):
        return self._scrollArea

    def setScrollArea(self, scrollArea):
        scrollArea.setWidget(self)
        self._scrollArea = scrollArea

    def _getCurrentRepresentation(self, glyph):
        name = self._cellRepresentationName
        args = self._cellRepresentationArguments
        args["width"] = self._cellWidth + 2 * self._cellWidthExtra
        args["height"] = self._cellHeight
        args["pixelRatio"] = self.devicePixelRatio()

        self._cellSizeCache.add((args["width"], args["height"]))
        return glyph.getRepresentation(name, **args)

    def preloadGlyphCellImages(self):
        """
        This preloads the glyphs’ current cell representations in the defcon
        representations_ cache.

        .. _representations: http://ts-defcon.readthedocs.org/en/ufo3/concepts/representations.html
        """
        for glyph in self._glyphs:
            self._getCurrentRepresentation(glyph)

    def glyphs(self):
        """
        Returns the list of glyphs displayed by this widget.
        """
        return self._glyphs

    def setGlyphs(self, glyphs):
        """
        Sets the list of Glyph_ *glyphs* displayed by this widget.

        The widget will try to preserve selection across the changing glyph
        set.

        The default is [].

        .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
        """
        currentSelection = [self._glyphs[index] for index in self._selection]
        newSelection = {
            glyphs.index(glyph) for glyph in currentSelection if glyph in glyphs
        }
        self._glyphs = glyphs
        self.setSelection(newSelection)
        self.adjustSize()

    def glyphsForIndexes(self, indexes):
        """
        Returns a list of glyphs that are at *indexes*.

        Indexes must be in range(len(glyphs)).
        """
        return [self._glyphs[i] for i in indexes]

    def cellSize(self):
        """
        Returns a tuple of *(cellWidth, cellHeight)*.
        """
        return self._cellWidth, self._cellHeight

    def setCellSize(self, width, height=None):
        """
        Sets the cellWidth to *width* and cellHeight to *height*.

        If *height* is None, cellHeight will be assigned *width*.

        The default is 50.
        """
        if height is None:
            height = width
        self._cellWidth = width
        self._cellHeight = height
        self._calculateCellWidthExtra()
        self._checkFlushCache()
        self.adjustSize()

    def cellRepresentationName(self):
        """
        Returns the name of the current glyph cell representation.
        """
        return self._cellRepresentationName

    def setCellRepresentationName(self, name):
        """
        Sets the name of the current glyph cell representation.

        The default is "defconQt.GlyphCell".
        """
        self._cellRepresentationName = name
        self.update()

    def cellRepresentationArguments(self):
        """
        Returns the current arguments passed to the glyph cell
        representationFactory.

        The default is {}.
        """
        return self._cellRepresentationArguments

    def setCellRepresentationArguments(self, kwargs):
        """
        Sets the arguments that will be passed to the glyph cell
        representationFactory.

        *kwargs* should be a dict.
        """
        self._cellRepresentationArguments = kwargs
        self.update()

    # selection

    def selection(self):
        """
        Returns a list of the current selection indexes, in ascending order.
        """
        return sorted(self._selection)

    def setSelection(self, selection, lastSelectedCell=None):
        """
        Sets this widget’s selection to a set of indexes *selection*.

        *lastSelectedCell* can be specified as an index that’s a member of the
        *selection* set, otherwise it will be set to min(selection) or None if
        *selection* is an empty set.

        The default *selection* is set(). The default *lastSelectedCell*
        is None.
        """
        self._selection = set(selection)
        if lastSelectedCell is not None:
            assert lastSelectedCell in self._selection
            self._lastSelectedCell = lastSelectedCell
        else:
            # fallback
            if not selection:
                self._lastSelectedCell = None
            else:
                self._lastSelectedCell = min(self._selection)
        if self._lastSelectedCell is not None:
            self.scrollToCell(self._lastSelectedCell)
        self.selectionChanged.emit()
        self.update()

    def lastSelectedCell(self):
        return self._lastSelectedCell

    def lastSelectedGlyph(self):
        cell = self._lastSelectedCell
        if cell is not None:
            return self._glyphs[cell]
        return None

    def _calculateCellWidthExtra(self):
        if self._columnCount:
            rem = self.width() % self._cellWidth
            self._cellWidthExtra = rem // (2 * self._columnCount)
        else:
            self._cellWidthExtra = 0

    def _checkFlushCache(self):
        if len(self._cellSizeCache) >= cacheBustSize:
            for glyph in self._glyphs:
                glyph.destroyRepresentation(self._cellRepresentationName)
            self._cellSizeCache = set()

    # ----------
    # Qt methods
    # ----------

    def sizeHint(self):
        parent = self.parent()
        width = parent.width() if parent is not None else self.width()
        if self._glyphs:
            columnCount = int(width / self._cellWidth)
            if columnCount == 0:
                columnCount = 1
            if columnCount > len(self._glyphs):
                columnCount = len(self._glyphs)
            rowCount = len(self._glyphs) // columnCount
            if columnCount * rowCount < len(self._glyphs):
                rowCount += 1
            newWidth = self._cellWidth * columnCount
            newHeight = self._cellHeight * rowCount
        else:
            columnCount = 0
            rowCount = 0
            newWidth = newHeight = 0
        self._columnCount = columnCount
        self._rowCount = rowCount
        return QSize(newWidth, newHeight)

    def paintEvent(self, event):
        painter = QPainter(self)
        visibleRect = event.rect()
        columnCount = self._columnCount
        extra = self._cellWidthExtra
        cellWidth, cellHeight = self._cellWidth + 2 * extra, self._cellHeight
        glyphCount = len(self._glyphs)
        if columnCount:
            paintWidth = min(glyphCount, columnCount) * cellWidth
        else:
            paintWidth = 0
        left = 0
        top = cellHeight

        painter.fillRect(visibleRect, Qt.white)
        for index, glyph in enumerate(self._glyphs):
            t = top - cellHeight
            rect = (left, t, cellWidth, cellHeight)

            if visibleRect.intersects(visibleRect.__class__(*rect)):
                if index in self._selection:
                    palette = self.palette()
                    active = palette.currentColorGroup() != QPalette.Inactive
                    opacityMultiplier = platformSpecific.colorOpacityMultiplier()
                    selectionColor = palette.color(QPalette.Highlight)
                    # TODO: alpha values somewhat arbitrary (here and in
                    # glyphLineView)
                    selectionColor.setAlphaF(0.2 * opacityMultiplier if active else 0.7)
                    painter.fillRect(
                        QRectF(left, t, cellWidth, cellHeight), selectionColor
                    )

                pixmap = self._getCurrentRepresentation(glyph)
                painter.drawPixmap(left, t, pixmap)

                # XXX: this hacks around the repr internals
                if (
                    index in self._selection
                    and cellHeight >= GlyphCellMinHeightForHeader
                ):
                    painter.fillRect(
                        QRectF(
                            left,
                            t + cellHeight - GlyphCellHeaderHeight,
                            cellWidth,
                            GlyphCellHeaderHeight,
                        ),
                        selectionColor,
                    )

            left += cellWidth
            if left + cellWidth > paintWidth:
                left = 0
                top += cellHeight

        # drop insertion position
        dropIndex = self._currentDropIndex
        if dropIndex is not None:
            if columnCount:
                x = (dropIndex % columnCount) * cellWidth
                y = (dropIndex // columnCount) * cellHeight
                # special-case the end-column
                if (
                    dropIndex == glyphCount
                    and glyphCount < self.width() // self._cellWidth
                    or self.mapFromGlobal(QCursor.pos()).y() < y
                ):
                    x = columnCount * cellWidth
                    y -= cellHeight
            else:
                x = y = 0
            path = QPainterPath()
            path.addRect(x - 2, y, 3, cellHeight)
            path.addEllipse(x - 5, y - 5, 9, 9)
            path.addEllipse(x - 5, y + cellHeight - 5, 9, 9)
            path.setFillRule(Qt.WindingFill)
            pen = painter.pen()
            pen.setColor(Qt.white)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.drawPath(path)
            painter.fillPath(path, insertionPositionColor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._calculateCellWidthExtra()

    # ---------
    # Selection
    # ---------

    def _linearSelection(self, index):
        if not self._selection:
            newSelection = {index}
        else:
            if index < self._lastSelectedCell:
                newSelection = self._selection | set(
                    range(index, self._lastSelectedCell + 1)
                )
            else:
                newSelection = self._selection | set(
                    range(self._lastSelectedCell, index + 1)
                )
        return newSelection

    def scrollToCell(self, index):
        """
        Scrolls the parent QScrollArea_ to show the glyph cell at *index*, if
        suitable parent widget is present.

        .. _QScrollArea: http://doc.qt.io/qt-5/qscrollarea.html
        """
        cellWidth, cellHeight = self._cellWidth, self._cellHeight
        scrollArea = self._scrollArea

        x = (0.5 + index % self._columnCount) * cellWidth
        y = (0.5 + index // self._columnCount) * cellHeight
        if scrollArea is not None:
            scrollArea.ensureVisible(x, y, cellWidth, cellHeight)

    # mouse

    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self._oldSelection = set(self._selection)
            index = self._findIndexForEvent(event)
            modifiers = event.modifiers()

            if index is None:
                if not (modifiers & Qt.ControlModifier or modifiers & Qt.ShiftModifier):
                    # TODO: consider setSelection(None)
                    self.setSelection(set())
                return

            if modifiers & Qt.ControlModifier:
                if index in self._selection:
                    self._selection.remove(index)
                else:
                    self._selection.add(index)
            elif modifiers & Qt.ShiftModifier:
                self._selection = self._linearSelection(index)
            elif index not in self._selection:
                self._selection = {index}
            else:
                self._maybeDragPosition = event.localPos()
            self._lastSelectedCell = index
            self.selectionChanged.emit()
            self.update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & (Qt.LeftButton | Qt.RightButton):
            index = self._findIndexForEvent(event, True)
            if index == self._lastSelectedCell:
                return
            if self.maybeExecuteDrag(event):
                return
            self.scrollToCell(index)
            if index >= len(self._glyphs):
                return

            modifiers = event.modifiers()
            if modifiers & Qt.ControlModifier:
                if index in self._selection and index in self._oldSelection:
                    self._selection.remove(index)
                elif index not in self._selection and index not in self._oldSelection:
                    self._selection.add(index)
            elif modifiers & Qt.ShiftModifier:
                self._selection = self._linearSelection(index)
            else:
                self._selection = {index}
            self._lastSelectedCell = index
            self.selectionChanged.emit()
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self._maybeDragPosition = None
            # XXX: we should use modifiers registered on click
            if not event.modifiers() & Qt.ShiftModifier:
                if self._lastSelectedCell is not None:
                    self._selection = {self._lastSelectedCell}
                else:
                    self._selection = set()
                self.update()
            self._oldSelection = None
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            index = self._findIndexForEvent(event)
            if index is not None:
                self.glyphActivated.emit(self._glyphs[index])
        else:
            super().mouseDoubleClickEvent(event)

    def _findIndexForEvent(self, event, allowAllViewport=False):
        cellHeight, cellWidth = (
            self._cellHeight,
            self._cellWidth + self._cellWidthExtra * 2,
        )
        glyphCount = len(self._glyphs)
        x, y = event.x(), event.y()
        visibleWidth = min(glyphCount, self._columnCount) * cellWidth
        if (
            not allowAllViewport or self._lastSelectedCell is None
        ) and x >= visibleWidth:
            return None
        x = max(0, min(event.x(), visibleWidth - 1))
        y = max(0, min(event.y(), self.height() - 1))
        index = (y // cellHeight) * self._columnCount + x // cellWidth
        if not allowAllViewport and index >= glyphCount:
            return None
        return index

    # key

    def selectAll(self):
        """
        Selects all glyphs displayed by this widget.
        """
        newSelection = set(range(len(self._glyphs)))
        self.setSelection(newSelection)

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            self._arrowKeyPressEvent(event)
        elif key == Qt.Key_Return:
            index = self._lastSelectedCell
            if index is not None:
                self.glyphActivated.emit(self._glyphs[index])
        elif modifiers in (Qt.NoModifier, Qt.ShiftModifier):
            self._glyphNameInputEvent(event)
        else:
            super().keyPressEvent(event)

    def _arrowKeyPressEvent(self, event):
        count = event.count()
        key = event.key()
        modifiers = event.modifiers()
        # TODO: it might be the case that self._lastSelectedCell cannot be None
        # when we arrive here whatsoever
        if self._lastSelectedCell is not None:
            if key == Qt.Key_Up:
                delta = -self._columnCount
            elif key == Qt.Key_Down:
                delta = self._columnCount
            elif key == Qt.Key_Left:
                delta = -1
            elif key == Qt.Key_Right:
                delta = 1
            newSel = self._lastSelectedCell + delta * count
            if newSel < 0 or newSel >= len(self._glyphs):
                return
            if modifiers & Qt.ShiftModifier:
                self._selection |= self._linearSelection(newSel)
            else:
                self._selection = {newSel}
            self._lastSelectedCell = newSel
            self.scrollToCell(newSel)
            self.selectionChanged.emit()
            self.update()

    def _glyphNameInputEvent(self, event):
        inputText = event.text()
        if not self._isUnicodeChar(inputText):
            return
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
        self._inputString = self._inputString + inputText

        match = None
        matchIndex = None
        lastResort = None
        lastResortIndex = None
        for index, glyph in enumerate(self._glyphs):
            item = glyph.name
            if item is None:
                continue
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
        else:
            return
        self.setSelection({newSelection})

    def _isUnicodeChar(self, char):
        return len(char) and unicodedata.category(char) != "Cc"

    # -------------
    # Drag and drop
    # -------------

    def maybeExecuteDrag(self, event):
        if self._maybeDragPosition is None:
            return False
        if (
            event.localPos() - self._maybeDragPosition
        ).manhattanLength() < QApplication.startDragDistance():
            return False

        drag = QDrag(self)
        glyphs = self.glyphsForIndexes(self.selection())
        mimeData = GlyphsMimeData()
        mimeData.setGlyphs(glyphs)
        drag.setMimeData(mimeData)
        drag.exec_()
        self._maybeDragPosition = None
        return True

    def dragEnterEvent(self, event):
        if event.source() == self:
            # glyph reordering
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        pos = event.pos()
        dropIndex = int(
            self._columnCount * (pos.y() // self._cellHeight)
            + (pos.x() + 0.5 * self._cellWidth) // self._cellWidth
        )
        self._currentDropIndex = min(dropIndex, len(self._glyphs))
        self.update()

    def dragLeaveEvent(self, event):
        self._currentDropIndex = None
        self.update()

    def dropEvent(self, event):
        insert = self._currentDropIndex
        newGlyphs = event.mimeData().glyphs()
        # put all glyphs to be moved to None (deleting them would
        # invalidate our insert indexes)
        if event.source() == self:
            selection = self._selection
            if selection:
                for index in selection:
                    self._glyphs[index] = None
        # insert newGlyphs into the list
        lst = self._glyphs[:insert] + newGlyphs + self._glyphs[insert:]
        self._glyphs = lst
        # now, elide None
        self._currentDropIndex = None
        self._glyphs = [glyph for glyph in self._glyphs if glyph is not None]
        self.setSelection(set())
        self.glyphsDropped.emit()
        self.update()


class GlyphCellView(QScrollArea):
    """
    The :class:`GlyphCellView` widget is a QScrollArea_ that contains a
    :class:`GlyphCellWidget`.

    It reimplements :class:`GlyphLineWidget` public API.

    Here’s an example that displays the glyphs of a Font_ in a
    :class:`GlyphLineView`:

    >>> from defconQt.controls.glyphCellView import GlyphCellView
    >>> window = BaseWindow()
    >>> glyphs = [font[name] for name in font.keys()]
    >>> view = GlyphCellView(window)
    >>> view.setGlyphs(glyphs)
    >>>
    >>> layout = QVBoxLayout(window)
    >>> layout.addWidget(view)
    >>> window.show()

    TODO: add sample image

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    .. _QScrollArea: http://doc.qt.io/qt-5/qscrollarea.html
    """

    glyphCellWidgetClass = GlyphCellWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        self._glyphCellWidget = self.glyphCellWidgetClass(self)
        self._glyphCellWidget.setScrollArea(self)
        # reexport signals
        self.glyphActivated = self._glyphCellWidget.glyphActivated
        self.glyphsDropped = self._glyphCellWidget.glyphsDropped
        self.selectionChanged = self._glyphCellWidget.selectionChanged

    # -------------
    # Notifications
    # -------------

    def _subscribeToGlyphs(self, glyphs):
        handledGlyphs = set()
        handledFonts = set()
        for glyph in glyphs:
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            font = glyph.font
            if font is None:
                continue
            if font in handledFonts:
                continue
            handledFonts.add(font)
            font.info.addObserver(self, "_fontChanged", "Info.Changed")

    def _unsubscribeFromGlyphs(self):
        handledGlyphs = set()
        handledFonts = set()
        if self._glyphCellWidget is not None:
            glyphs = self._glyphCellWidget.glyphs()
            for glyph in glyphs:
                if glyph in handledGlyphs:
                    continue
                handledGlyphs.add(glyph)
                glyph.removeObserver(self, "Glyph.Changed")
                font = glyph.font
                if font is None:
                    continue
                if font in handledFonts:
                    continue
                handledFonts.add(font)
                font.info.removeObserver(self, "Info.Changed")

    def _glyphChanged(self, notification):
        self._glyphCellWidget.update()

    def _fontChanged(self, notification):
        info = notification.object
        font = info.font
        glyphs = self._glyphCellWidget.glyphs()
        representationName = self._glyphCellWidget.cellRepresentationName()
        for glyph in glyphs:
            if glyph.font == font:
                glyph.destroyRepresentation(representationName)
        self._glyphCellWidget.update()

    # --------------
    # Public methods
    # --------------

    def preloadGlyphCellImages(self):
        self._glyphCellWidget.preloadGlyphCellImages()

    def glyphs(self):
        return self._glyphCellWidget.glyphs()

    def setGlyphs(self, glyphs):
        self._unsubscribeFromGlyphs()
        self._glyphCellWidget.setGlyphs(glyphs)
        self._subscribeToGlyphs(glyphs)

    def glyphsForIndexes(self, indexes):
        return self._glyphCellWidget.glyphsForIndexes(indexes)

    def cellSize(self):
        return self._glyphCellWidget.cellSize()

    def setCellSize(self, width, height=None):
        self._glyphCellWidget.setCellSize(width, height)

    def cellRepresentationName(self):
        return self._glyphCellWidget.cellRepresentationName()

    def setCellRepresentationName(self, name):
        self._glyphCellWidget.setCellRepresentationName(name)

    def cellRepresentationArguments(self):
        return self._glyphCellWidget.cellRepresentationArguments()

    def setCellRepresentationArguments(self, kwargs):
        self._glyphCellWidget.setCellRepresentationArguments(kwargs)

    def selection(self):
        return self._glyphCellWidget.selection()

    def setSelection(self, selection, lastSelectedCell=None):
        self._glyphCellWidget.setSelection(selection, lastSelectedCell)

    def lastSelectedCell(self):
        return self._glyphCellWidget.lastSelectedCell()

    def lastSelectedGlyph(self):
        return self._glyphCellWidget.lastSelectedGlyph()

    def selectAll(self):
        self._glyphCellWidget.selectAll()

    # ----------
    # Qt methods
    # ----------

    def setAcceptDrops(self, value):
        self._glyphCellWidget.setAcceptDrops(value)
