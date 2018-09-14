from math import ceil
import time
from trufont.util import drawing
import wx
from unicodedata import category

__all__ = ["GlyphCellView"]

GlyphActivatedEvent, EVT_GLYPH_ACTIVATED = wx.lib.newevent.NewEvent()
SelectionChangedEvent, EVT_SELECTION_CHANGED = wx.lib.newevent.NewEvent()


class GlyphCellView(wx.ScrolledCanvas):
    GLYPH_ACTIVATED = EVT_GLYPH_ACTIVATED
    SELECTION_CHANGED = EVT_SELECTION_CHANGED

    def __init__(self, parent):
        super().__init__(parent, style=wx.WANTS_CHARS)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(wx.EVT_SET_FOCUS, lambda _: self.Refresh())
        self.Bind(wx.EVT_KILL_FOCUS, lambda _: self.Refresh())
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetBackgroundColour(wx.WHITE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)
        self.SetScrollRate(50, 50)

        self._cellWidth = 86
        self._cellHeight = 86
        self._extraCellWidth = 0
        self._glyphs = []

        self._inputString = ""
        self._lastKeyInputTime = None
        self._activeCell = None
        self._selection = set()

        self._columnCount = 0
        self._rowCount = 0

    @property
    def cellSize(self):
        return self._cellWidth, self._cellHeight

    @cellSize.setter
    def cellSize(self, value):
        if isinstance(value, tuple):
            width, height = value
        else:
            width = height = value
        self._cellWidth = width
        self._cellHeight = height
        self._adjustSize()
        self._calculateExtraCellWidth()
        self.Refresh()

    @property
    def glyphs(self):
        return self._glyphs

    @glyphs.setter
    def glyphs(self, glyphs):
        self._glyphs = glyphs
        self.selection = set()
        self._adjustSize()
        self.Refresh()

    @property
    def activeCell(self):
        return self._activeCell

    @activeCell.setter
    def activeCell(self, value):
        assert value in self._selection
        self._activeCell = value
        # self.Refresh()

    @property
    def activeLayer(self):
        cell = self._activeCell
        if cell is not None:
            return self._glyphs[cell].layerForMaster(None)

    @property
    def selection(self):
        return set(self._selection)

    @selection.setter
    def selection(self, selection):
        self._selection = selection
        if selection:
            self._activeCell = min(selection)
            self.scrollToCell(self._activeCell)
        else:
            self._activeCell = None
        wx.PostEvent(self, SelectionChangedEvent(selection=selection))
        self.Refresh()

    def glyphsForIndexes(self, indexes):
        """
        Returns a list of glyphs that are at *indexes*.

        Indexes must be in range(len(glyphs)).
        """
        return [self._glyphs[i] for i in indexes]

    def scrollToCell(self, index):
        cellHeight = self._cellHeight + 1
        yMin = index // self._columnCount * cellHeight
        _, viewMin = self.CalcScrolledPosition(0, yMin)
        if viewMin < 0:
            pxPerUnits = self.GetScrollPixelsPerUnit()[1]
            y = self.GetViewStart()[1] * pxPerUnits
            y += viewMin
            self.Scroll(-1, y / pxPerUnits)
            return
        yMax = yMin + cellHeight
        _, viewMax = self.CalcScrolledPosition(0, yMax)
        currentMax = self.GetClientSize()[1]
        if viewMax >= currentMax:
            pxPerUnits = self.GetScrollPixelsPerUnit()[1]
            y = self.GetViewStart()[1] * pxPerUnits
            y += viewMax - currentMax
            self.Scroll(-1, ceil(y / pxPerUnits))

    def selectAll(self):
        self.selection = set(range(len(self._glyphs)))

    # --------------
    # Helper methods
    # --------------

    def _adjustSize(self):
        width, _ = self.GetClientSize()
        if self._glyphs:
            columnCount = width // self._cellWidth
            glyphCount = len(self._glyphs)
            # check for the gap
            if columnCount:
                rem = width - self._cellWidth * columnCount - (columnCount - 1)
                if rem < 0:
                    columnCount -= 1
            if columnCount == 0:
                columnCount = 1
            if columnCount > glyphCount:
                columnCount = glyphCount
            rowCount = glyphCount // columnCount
            if columnCount * rowCount < glyphCount:
                rowCount += 1
            newWidth = self._cellWidth * columnCount
            newHeight = self._cellHeight * rowCount + (rowCount - 1)
        else:
            columnCount = 0
            rowCount = 0
            newWidth = newHeight = 0
        self._columnCount = columnCount
        self._rowCount = rowCount
        self.SetVirtualSize(newWidth, newHeight)
        self.Refresh()

    def _arrowKeyDown(self, event):
        key = event.GetKeyCode()
        modifiers = event.GetModifiers()
        # TODO: it might be the case that self._activeCell cannot be None
        # when we arrive here whatsoever
        activeCell = self._activeCell
        if activeCell is None:
            activeCell = 0
        if key == wx.WXK_UP:
            delta = -self._columnCount
        elif key == wx.WXK_DOWN:
            delta = self._columnCount
        elif key == wx.WXK_LEFT:
            delta = -1
        elif key == wx.WXK_RIGHT:
            delta = 1
        newSel = activeCell + delta
        if newSel < 0 or newSel >= len(self._glyphs):
            return
        self._activeCell = activeCell
        if modifiers & wx.MOD_SHIFT:
            self._selection |= self._linearSelection(newSel)
        else:
            self._selection = {newSel}
        self._activeCell = newSel
        self.scrollToCell(newSel)
        wx.PostEvent(self, SelectionChangedEvent(selection=self._selection))
        self.Refresh()

    def _calculateExtraCellWidth(self):
        columnCount = self._columnCount
        if columnCount:
            width, _ = self.GetClientSize()
            rem = (width - (columnCount - 1)) % self._cellWidth
            extraCellWidth = rem // (2 * columnCount)
        else:
            extraCellWidth = 0
        if extraCellWidth == self._extraCellWidth:
            return
        self._extraCellWidth = extraCellWidth
        self.Refresh()

    def _indexForPosition(self, pos, allowAllViewport=False):
        pos = self.CalcUnscrolledPosition(pos)
        cellHeight = self._cellHeight + 1
        cellWidth = self._cellWidth + self._extraCellWidth * 2 + 1
        glyphCount = len(self._glyphs)
        visibleWidth = min(glyphCount, self._columnCount) * (cellWidth - 1)
        _, height = self.GetVirtualSize()
        if (not allowAllViewport or self._activeCell is None) and pos.x >= visibleWidth:
            return None
        x = max(0, min(pos.x, visibleWidth - 1))
        y = max(0, min(pos.y, height - 1))
        index = (y // cellHeight) * self._columnCount + x // cellWidth
        if not allowAllViewport and index >= glyphCount:
            return None
        return index

    def _linearSelection(self, index):
        try:
            selection = self._oldSelection
            activeCell = self._oldActiveCell
        except AttributeError:
            selection = self._selection
            activeCell = self._activeCell

        if not selection:
            newSelection = {index}
        else:
            if index < activeCell:
                newSelection = selection | set(range(index, activeCell + 1))
            else:
                newSelection = selection | set(range(activeCell, index + 1))
        return newSelection

    # ----------
    # wx methods
    # ----------

    def OnChar(self, event):
        key = event.GetUnicodeKey()
        if key == wx.WXK_NONE:
            return
        inputText = chr(key)
        if category(inputText) == "Cc":
            return
        rightNow = time.time()
        if self._lastKeyInputTime is None:
            self._lastKeyInputTime = rightNow
        if rightNow - self._lastKeyInputTime > 0.75:
            self._inputString = ""
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
            if item.startswith(self._inputString):
                if match is None:
                    match = item
                    matchIndex = index
                    continue
                if item < match:
                    match = item
                    matchIndex = index
                    continue
            if item > self._inputString:
                if lastResort is None:
                    lastResort = item
                    lastResortIndex = index
                    continue
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
        self.selection = {newSelection}

    def OnPaint(self, event):
        rect = self.GetUpdateRegion().GetBox()
        rH = rect.GetHeight()
        if not rH:
            return
        dc = wx.PaintDC(self)
        self.DoPrepareDC(dc)
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.Clear()
        ctx = wx.GraphicsContext.Create(dc)
        ctx.GetFont = self.GetFont
        cellWidth = self._cellWidth + 2 * self._extraCellWidth
        cellHeight = self._cellHeight
        columnCount = self._columnCount

        w, _ = self.GetSize()
        ty = self.CalcUnscrolledPosition(rect.GetPosition())[1]
        by = ty + rH
        first = (ty // (cellHeight + 1)) * columnCount
        last = ceil(by / (cellHeight + 1)) * columnCount

        attr = wx.SYS_COLOUR_HIGHLIGHT if self.HasFocus() else wx.SYS_COLOUR_BTNSHADOW
        selectionColor = wx.SystemSettings.GetColour(attr)
        r, g, b, a = selectionColor.Get()
        selectionColor.Set(r, g, b, int(.2 * a))

        left, top = 0, ty - (ty % (cellHeight + 1))
        index = first
        selection = self._selection
        for glyph in self._glyphs[first:last]:
            color = selectionColor if index in selection else None
            ctx.PushState()
            ctx.Translate(left, top)
            drawing.drawGlyphFigure(ctx, glyph, cellWidth, cellHeight, color)
            ctx.PopState()

            left += cellWidth + 1
            if left + cellWidth > w:
                left = 0
                top += cellHeight + 1
            index += 1

        del ctx.GetFont

    def OnKeyDown(self, event):
        key = event.GetKeyCode()
        if event.IsKeyInCategory(wx.WXK_CATEGORY_ARROW):
            self._arrowKeyDown(event)
        elif key == wx.WXK_TAB:
            self.Navigate(not event.GetModifiers() & wx.MOD_SHIFT)
        elif key == wx.WXK_RETURN:
            index = self._activeCell
            if index is not None:
                wx.PostEvent(self, GlyphActivatedEvent(glyph=self._glyphs[index]))
        else:
            # let char event proceed
            event.Skip()

    def OnLeftDClick(self, event):
        index = self._indexForPosition(event.GetPosition())
        if index is not None:
            wx.PostEvent(self, GlyphActivatedEvent(glyph=self._glyphs[index]))

    def OnLeftDown(self, event):
        self._oldActiveCell = self._activeCell
        self._oldSelection = set(self._selection)
        index = self._indexForPosition(event.GetPosition())
        modifiers = event.GetModifiers()

        # let focus be set
        event.Skip()
        if index is None:
            if not (modifiers & wx.MOD_CONTROL or modifiers & wx.MOD_SHIFT):
                self.selection = set()
            return

        if modifiers & wx.MOD_CONTROL:
            if index in self._selection:
                self._selection.remove(index)
            else:
                self._selection.add(index)
        elif modifiers & wx.MOD_SHIFT:
            self._selection = self._linearSelection(index)
        elif index not in self._selection:
            self._selection = {index}
        self._activeCell = self._mouseDownCell = index
        wx.PostEvent(self, SelectionChangedEvent(selection=self._selection))
        self.Refresh()

    def OnLeftUp(self, event):
        if hasattr(self, "_mouseDownCell"):
            # XXX: use modifiers registered on click?
            if (
                not event.GetModifiers() & (wx.MOD_SHIFT | wx.MOD_CONTROL)
                and self._mouseDownCell == self._activeCell
                and self._mouseDownCell in self._oldSelection
            ):
                self._selection = {self._activeCell}
                wx.PostEvent(self, SelectionChangedEvent(selection=self._selection))
                self.Refresh()
            del self._mouseDownCell
        if hasattr(self, "_oldActiveCell"):
            del self._oldActiveCell
            del self._oldSelection

    def OnMotion(self, event):
        if event.LeftIsDown():
            index = self._indexForPosition(event.GetPosition(), True)
            if index == self._activeCell:
                return
            self.scrollToCell(index)
            if index >= len(self._glyphs):
                return

            modifiers = event.GetModifiers()
            if modifiers & wx.MOD_CONTROL:
                if index in self._selection and index in self._oldSelection:
                    self._selection.remove(index)
                elif index not in self._selection and index not in self._oldSelection:
                    self._selection.add(index)
            elif modifiers & wx.MOD_SHIFT:
                self._selection = self._linearSelection(index)
            else:
                self._selection = {index}
            self._activeCell = index
            wx.PostEvent(self, SelectionChangedEvent(selection=self._selection))
            self.Refresh()
        else:
            event.Skip()

    def OnSize(self, event):
        # on OSX, OnSize is called once before the ctor (nice)
        if not hasattr(self, "_glyphs"):
            return
        self._adjustSize()
        self._calculateExtraCellWidth()
