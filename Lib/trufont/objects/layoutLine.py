from PyQt5.QtCore import QObject
from defconQt.controls.glyphContextView import GlyphRecord
import array


def _reverseEnumerate(seq):
    n = len(seq)
    for obj in reversed(seq):
        n -= 1
        yield n, obj


class LayoutLine(QObject):
    engine = None

    def __init__(self, parent):
        super().__init__(parent)
        assert self.engine is not None, \
            "LayoutLine needs a shaping engine to work!"

        # this stays None except when we want to commit to widget
        self._activeIndex = None
        text = "".join(
            chr(glyph.unicode) if glyph.unicode is not None else
            glyph.name for glyph in parent.glyphs())
        self._inputString = array.array('u', text)
        self._caretIndex = len(text)
        self._needsLayout = False
        self.updateView()

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
            self._caretIndex = len(self._inputString)
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
            pos.setX(pos.x() + .5 * (record.xAdvance * widget.scale()))
            halfIndex = widget.indexForPoint(pos)
            if halfIndex == index:
                self._activeIndex = max(index - 1, 0)
                self._caretIndex = record.cluster
            else:
                self._activeIndex = index
                try:
                    self._caretIndex = glyphRecords[index + 1].cluster
                except IndexError:
                    self._caretIndex = len(self._inputString)
            self.updateView()

    def insert(self, text):
        self._inputString.insert(self._caretIndex, text)
        self._activeIndex = 1
        self._caretIndex += len(text)
        self._needsLayout = True
        self.updateView()

    def delete(self, forward=False):
        index = self._caretIndex - (not forward)
        if index < 0 or index >= len(self._inputString):
            return
        self._inputString.pop(index)
        self._caretIndex = index
        self._needsLayout = True
        self.updateView()

    #

    def drawingOffset(self, index):
        """
        Returns *(dx, dy)* offset if caret is to be drawn, or None otherwise.
        """
        glyphRecords = self.parent().glyphRecords()
        glyphRecord = glyphRecords[index]
        atRightBoundary = self._caretIndex == len(self._inputString)
        if glyphRecord.cluster != self._caretIndex and not \
                (atRightBoundary and index == len(glyphRecords) - 1):
            return None
        dx = -glyphRecord.xOffset
        dy = -glyphRecord.yOffset
        if atRightBoundary:
            dx += glyphRecord.xAdvance
            dy += glyphRecord.yAdvance
        return dx, dy

    #

    @property
    def _font(self):
        return self.parent().window().font_()

    @property
    def _shaper(self):
        if hasattr(self.engine, "_layoutEngine"):
            return 'compositor'
        return 'harfbuzz'

    def _lookupActiveIndex(self):
        for i, rec in _reverseEnumerate(self.parent().glyphRecords()):
            if rec.cluster <= self._caretIndex:
                return i
        raise ValueError("caret index cannot be matched!")

    def _shapeAndSetText(self):
        font = self._font
        records = self.engine.process(self._inputString.tounicode())
        if self._shaper == 'compositor':
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
        layoutPerformed = self._needsLayout
        if self._needsLayout:
            self._shapeAndSetText()
            self._needsLayout = False
        if self._activeIndex is not None:
            if layoutPerformed:
                self._activeIndex = self._lookupActiveIndex()
            widget.setActiveIndex(self._activeIndex)
            self._activeIndex = None
        widget.update()
