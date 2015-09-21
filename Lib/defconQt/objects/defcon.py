from defcon import Font, Contour, Glyph, Point
from defcon.objects.base import BaseObject

class TFont(Font):
    def __init__(self, *args, **kwargs):
        if not "glyphClass" in kwargs:
            kwargs["glyphClass"] = TGlyph
        if not "glyphContourClass" in kwargs:
            kwargs["glyphContourClass"] = TContour
        if not "glyphPointClass" in kwargs:
            kwargs["glyphPointClass"] = TPoint
        super(TFont, self).__init__(*args, **kwargs)

    # XXX: had to copy all of this so as to exclude template glyphs from
    # save. It pains me that's the only thing to be done w current upstream
    def save(self, path=None, formatVersion=None):
        saveAs = False
        if path is not None and path != self._path:
            saveAs = True
        else:
            path = self._path
        ## work out the format version
        # if None is given, fallback to the one that
        # came in when the UFO was loaded
        if formatVersion is None and self._ufoFormatVersion is not None:
            formatVersion = self._ufoFormatVersion
        # otherwise fallback to 2
        elif self._ufoFormatVersion is None:
            formatVersion = 2
        ## make a UFOWriter
        ufoWriter = ufoLib.UFOWriter(path, formatVersion=formatVersion)
        ## save objects
        saveInfo = False
        saveKerning = False
        saveGroups = False
        saveFeatures = False
        ## lib should always be saved
        saveLib = True
        # if in a save as, save all objects
        if saveAs:
            saveInfo = True
            saveKerning = True
            saveGroups = True
            saveFeatures = True
        ## if changing ufo format versions, save all objects
        if self._ufoFormatVersion != formatVersion:
            saveInfo = True
            saveKerning = True
            saveGroups = True
            saveFeatures = True
        # save info, kerning and features if they are dirty
        if self._info is not None and self._info.dirty:
            saveInfo = True
        if self._kerning is not None and self._kerning.dirty:
            saveKerning = True
        if self._features is not None and self._features.dirty:
            saveFeatures = True
        # always save groups and lib if they are loaded
        # as they contain sub-objects that may not notify
        # the main object about changes.
        if self._groups is not None:
            saveGroups = True
        if self._lib is not None:
            saveLib = True
        # save objects as needed
        if saveInfo:
            ufoWriter.writeInfo(self.info)
            self._stampInfoDataState()
            self.info.dirty = False
        if saveKerning:
            ufoWriter.writeKerning(self.kerning)
            self._stampKerningDataState()
            self.kerning.dirty = False
        if saveGroups:
            ufoWriter.writeGroups(self.groups)
            self._stampGroupsDataState()
        if saveFeatures and formatVersion > 1:
            ufoWriter.writeFeatures(self.features.text)
            self._stampFeaturesDataState()
        if saveLib:
            # if making format version 1, do some
            # temporary down conversion before
            # passing the lib to the writer
            libCopy = dict(self.lib)
            if formatVersion == 1:
                self._convertToFormatVersion1RoboFabData(libCopy)
            ufoWriter.writeLib(libCopy)
            self._stampLibDataState()
        ## save glyphs
        # for a save as operation, load all the glyphs
        # and mark them as dirty.
        if saveAs:
            for glyph in self:
                glyph.dirty = True
        glyphSet = ufoWriter.getGlyphSet()
        for glyphName, glyphObject in self._glyphs.items():
            if glyphObject.template: continue
            if glyphObject.dirty:
                glyphSet.writeGlyph(glyphName, glyphObject, glyphObject.drawPoints)
                self._stampGlyphDataState(glyphObject)
        # remove deleted glyphs
        if not saveAs and self._scheduledForDeletion:
            for glyphName in self._scheduledForDeletion:
                if glyphName in glyphSet:
                    glyphSet.deleteGlyph(glyphName)
        glyphSet.writeContents()
        self._glyphSet = glyphSet
        self._scheduledForDeletion = []
        self._path = path
        self._ufoFormatVersion = formatVersion
        self.dirty = False

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
    def __init__(self, pointClass=None):
        if pointClass is None:
            pointClass = TPoint
        super(TContour, self).__init__(pointClass)

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

    def __init__(self, pt, segmentType=None, smooth=False, name=None, selected=False):
        super(TPoint, self).__init__(pt, segmentType, smooth, name)
        self._selected = selected

    def _get_selected(self):
        return self._selected

    def _set_selected(self, value):
        self._selected = value

    selected = property(_get_selected, _set_selected, doc="A boolean indicating the selected state of the point.")

class CharacterSet(object):
    __slots__ = ["_name", "_glyphNames"]

    def __init__(self, glyphNames, name=None):
        self._name = name
        self._glyphNames = glyphNames

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name

    name = property(_get_name, _set_name, doc="Character set name.")

    def _get_glyphNames(self):
        return self._glyphNames

    def _set_glyphNames(self, glyphNames):
        self._glyphNames = glyphNames

    glyphNames = property(_get_glyphNames, _set_glyphNames, doc="List of glyph names.")
