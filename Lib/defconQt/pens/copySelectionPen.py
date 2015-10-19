from defconQt.objects.defcon import TGlyph
from robofab.pens.pointPen import AbstractPointPen


class CopySelectionPen(AbstractPointPen):

    def __init__(self, glyph=None):
        if glyph is None:
            glyph = TGlyph()
        self._glyph = glyph
        self._contour = None
        self._havePoint = False
        self._originalContourIsOpen = False

    def beginPath(self):
        self._contour = self._glyph.contourClass(
            pointClass=self._glyph.pointClass)

    def endPath(self, keepOpened=False):
        if self._havePoint:
            self.elideOrphanOffCurves(True)
            if self._originalContourIsOpen or keepOpened:
                self._contour[0].segmentType = "move"
            self._contour.dirty = False
            self._glyph.appendContour(self._contour)
        self._contour = None
        self._havePoint = False
        self._originalContourIsOpen = False

    def addPoint(self, pt, segmentType=None, smooth=False, name=None,
                 selected=False, **kwargs):
        if segmentType == "move":
            self._originalContourIsOpen = True
        if segmentType is None or selected:
            if selected:
                self._havePoint = True
            self._contour.addPoint(pt, segmentType, smooth, name)
        else:
            self.elideOrphanOffCurves(False)
            if self._havePoint:
                # We started drawing a path and we have a gap in it. Create
                # a new contour (and leave this one opened).
                self.endPath(True)
                self.beginPath()

    def addComponent(self, baseGlyphName, transformation):
        pass  # XXX

    def elideOrphanOffCurves(self, arrivedAtBoundary):
        # onCurves that aren't selected and preceding offCurves if any are
        # elided
        for _ in range(2):
            if len(self._contour):
                if len(self._contour) > 1 and arrivedAtBoundary and \
                        self._contour[0].segmentType == "curve":
                    # We're at the end of drawing and the offCurves lead to
                    # begin onCurve. Let them in.
                    pass
                elif self._contour[-1].segmentType is None:
                    self._contour.removePoint(self._contour[-1])

    def getGlyph(self):
        return self._glyph
