from defcon import Font, Contour, Glyph, Point
from defcon.objects.base import BaseObject
from fontTools.agl import AGL2UV

class TFont(Font):
    def __init__(self, *args, **kwargs):
        if not "glyphClass" in kwargs:
            kwargs["glyphClass"] = TGlyph
        if not "glyphContourClass" in kwargs:
            kwargs["glyphContourClass"] = TContour
        if not "glyphPointClass" in kwargs:
            kwargs["glyphPointClass"] = TPoint
        super(TFont, self).__init__(*args, **kwargs)

    def newStandardGlyph(self, name, override=False, addUnicode=True, asTemplate=False, width=500):
        if not override:
            if name in self:
                return None
        # XXX(defcon): newGlyph should return the glyph
        self.newGlyph(name)
        glyph = self[name]
        glyph.width = width
        # TODO: list ought to be changeable from AGL2UV
        if addUnicode:
            if name in AGL2UV:
                glyph.unicode = AGL2UV[name]
        glyph.template = asTemplate
        return glyph

    # TODO: stop using that workaround now that we're ufo3
    def save(self, path=None, formatVersion=None):
        for glyph in self:
            if glyph.template:
                glyph.dirty = False
        super(TFont, self).save(path, formatVersion)

class TGlyph(Glyph):
    def __init__(self, *args, **kwargs):
        super(TGlyph, self).__init__(*args, **kwargs)
        self._template = False

    def _get_template(self):
        return self._template

    def _set_template(self, value):
        self._template = value

    template = property(_get_template, _set_template, doc="A boolean indicating whether the glyph is a template glyph.")

    def _set_dirty(self, value):
        BaseObject._set_dirty(self, value)
        if value:
            self.template = False

    dirty = property(BaseObject._get_dirty, _set_dirty)

class TContour(Contour):
    def __init__(self, pointClass=None, **kwargs):
        if pointClass is None:
            pointClass = TPoint
        super(TContour, self).__init__(pointClass=pointClass, **kwargs)

    def drawPoints(self, pointPen):
        """
        Draw the contour with **pointPen**.
        """
        pointPen.beginPath()
        for point in self._points:
            pointPen.addPoint((point.x, point.y), segmentType=point.segmentType, smooth=point.smooth, name=point.name, selected=point.selected)
        pointPen.endPath()

class TPoint(Point):
    __slots__ = ["_selected"]

    def __init__(self, pt, selected=False, **kwargs):
        super(TPoint, self).__init__(pt, **kwargs)
        self._selected = selected

    def _get_selected(self):
        return self._selected

    def _set_selected(self, value):
        self._selected = value

    selected = property(_get_selected, _set_selected, doc="A boolean indicating the selected state of the point.")

class GlyphSet(object):
    __slots__ = ["_name", "_glyphNames"]

    def __init__(self, glyphNames, name=None):
        self._name = name
        self._glyphNames = glyphNames

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name

    name = property(_get_name, _set_name, doc="Glyph set name.")

    def _get_glyphNames(self):
        return self._glyphNames

    def _set_glyphNames(self, glyphNames):
        self._glyphNames = glyphNames

    glyphNames = property(_get_glyphNames, _set_glyphNames, doc="List of glyph names.")
