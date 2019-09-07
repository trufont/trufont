from PyQt5.QtCore import QObject

from defconQt.controls.glyphContextView import GlyphRecord


def _reverseEnumerate(seq):
    n = len(seq)
    for obj in reversed(seq):
        n -= 1
        yield n, obj


# TODO: support unencoded glyphs input
# TODO: support RTL (caret)
# TODO: support selection


class LayoutManager(QObject):
    """
    parent should be a GlyphContextView.
    """

    def __init__(self, font, parent):
        super().__init__(parent)
        self._font = font
        # this stays None except when we want to commit to widget
        self._activeIndex = None
        self._caretIndex = 0
        self._glyphList = []
        self._needsCaretPostFix = False
        self._needsLayout = False
        self.updateView()

    def glyphList(self):
        return self._glyphList

    def setGlyphList(self, glyphNames):
        self._glyphList = glyphNames
        self._caretIndex = len(self._glyphList)
        self._needsLayout = True
        self.updateView()

    #

    def initCaret(self):
        """
        aka. setCaretFromActiveIndex
        """
        widget = self.parent()
        index = widget.activeIndex()
        glyphRecords = widget.glyphRecords()
        try:
            self._caretIndex = glyphRecords[index + 1].cluster
        except IndexError:
            self._caretIndex = len(self._glyphList)

    def caretNext(self):
        widget = self.parent()
        # TODO: this could be a binary search
        for i, rec in enumerate(widget.glyphRecords()):
            if rec.cluster > self._caretIndex:
                self._activeIndex = i - 1
                self._caretIndex = rec.cluster
                break
        # TODO: trim no-op updates?
        if self._activeIndex is None:
            self._activeIndex = i
            self._caretIndex = len(self._glyphList)
        self.updateView()

    def caretPrevious(self):
        widget = self.parent()
        # TODO: this could be a binary search
        for i, rec in _reverseEnumerate(widget.glyphRecords()):
            if rec.cluster < self._caretIndex:
                self._activeIndex = max(i - 1, 0)
                self._caretIndex = rec.cluster
                break
        if self._activeIndex is None:
            # we're at left boundary
            return
        self.updateView()

    def setCaretFromPos(self, pos):
        """
        *pos* is provided in parent coordinates.
        """
        widget = self.parent()
        index = widget.indexForPoint(pos)
        if index is not None:
            glyphRecords = widget.glyphRecords()
            record = glyphRecords[index]
            pos.setX(pos.x() + 0.5 * (record.xAdvance * widget.scale()))
            halfIndex = widget.indexForPoint(pos)
            if halfIndex == index:
                self._activeIndex = max(index - 1, 0)
                self._caretIndex = record.cluster
            else:
                self._activeIndex = index
                try:
                    self._caretIndex = glyphRecords[index + 1].cluster
                except IndexError:
                    self._caretIndex = len(self._glyphList)
            self.updateView()

    def insert(self, content):
        if isinstance(content, list):
            self._glyphList[self._caretIndex : self._caretIndex] = content
            self._caretIndex += len(content)
        else:
            self._glyphList.insert(self._caretIndex, content)
            self._caretIndex += 1
        # clamp caretIndex after shaping and set activeIndex
        # typ. when we input text that serves as prefix to a ligature
        self._needsCaretPostFix = True
        self._needsLayout = True
        self.updateView()

    def delete(self, forward=False):
        index = self._caretIndex - (not forward)
        if index < 0 or index >= len(self._glyphList):
            return
        self._glyphList.pop(index)
        self._caretIndex = index
        self._needsCaretPostFix = True
        self._needsLayout = True
        self.updateView()

    #

    def drawingOffset(self, index):
        """
        Returns *(dx, dy)* offset if caret is to be drawn, or None otherwise.
        """
        glyphRecords = self.parent().glyphRecords()
        glyphRecord = glyphRecords[index]
        atRightBoundary = self._caretIndex == len(self._glyphList)
        if glyphRecord.cluster != self._caretIndex and not (
            atRightBoundary and index == len(glyphRecords) - 1
        ):
            return None
        dx = -glyphRecord.xOffset
        dy = -glyphRecord.yOffset
        if atRightBoundary:
            dx += glyphRecord.xAdvance
            dy += glyphRecord.yAdvance
        return dx, dy

    #

    @property
    def _shaper(self):
        engine = self._font.engine
        if engine is None:
            return None
        if hasattr(engine, "_layoutEngine"):
            return "compositor"
        return "harfbuzz"

    def _shapeAndSetText(self):
        font = self._font
        records = font.engine.process(self._glyphList)
        if self._shaper == "compositor":
            records_ = []
            index = 0
            for glyphRecord in records:
                record_ = GlyphRecord()
                record_.glyph = glyph = font[glyphRecord.glyphName]
                record_.cluster = index
                record_.xOffset = glyphRecord.xPlacement
                record_.yOffset = glyphRecord.yPlacement
                record_.xAdvance = glyph.width + glyphRecord.xAdvance
                record_.yAdvance = glyph.height + glyphRecord.yAdvance
                records_.append(record_)
                index += len(glyphRecord.ligatureComponents) or 1
            records = records_
        self.parent().setGlyphRecords(records)

    def updateView(self):
        widget = self.parent()
        if self._needsLayout:
            font = self._font
            if font.engine is not None:
                self._shapeAndSetText()
            else:
                glyphs = []
                for glyphName in self._glyphList:
                    if glyphName in font:
                        glyphs.append(font[glyphName])
                widget.setGlyphs(glyphs)
            self._needsLayout = False
        if self._needsCaretPostFix:
            glyphRecords = widget.glyphRecords()
            for i, rec in enumerate(glyphRecords):
                if rec.cluster >= self._caretIndex:
                    self._activeIndex = max(i - 1, 0)
                    self._caretIndex = rec.cluster
                    break
            if self._activeIndex is None:
                self._activeIndex = max(len(glyphRecords) - 1, 0)
            self._needsCaretPostFix = False
        if self._activeIndex is not None:
            widget.setActiveIndex(self._activeIndex)
            self._activeIndex = None
        widget.update()
