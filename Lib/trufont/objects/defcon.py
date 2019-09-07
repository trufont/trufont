import math
import types

import fontTools
from booleanOperations import union
from defcon import (
    Anchor,
    Component,
    Contour,
    Font,
    Glyph,
    Groups,
    Guideline,
    Image,
    Kerning,
    Layer,
    Point,
)
from fontTools.misc.transform import Identity
from PyQt5.QtWidgets import QApplication
from ufo2ft import compileOTF, compileTTF

from trufont.objects import settings
from trufont.objects.undoManager import UndoManager

_shaper = True
try:
    import harfbuzz  # noqa
    from trufont.objects.layoutEngine import LayoutEngine
except ImportError:
    try:
        import compositor  # noqa
        from defcon import LayoutEngine
    except ImportError:
        _shaper = False


class TFont(Font):
    def __init__(self, *args, **kwargs):
        # TODO: maybe subclass all objects into our own for caller stability
        attrs = (
            ("glyphAnchorClass", TAnchor),
            ("glyphComponentClass", TComponent),
            ("glyphClass", TGlyph),
            ("glyphContourClass", TContour),
            ("glyphPointClass", TPoint),
            ("glyphImageClass", TImage),
            ("guidelineClass", TGuideline),
            ("layerClass", TLayer),
            ("groupsClass", TGroups),
            ("kerningClass", TKerning),
        )
        for attr, defaultClass in attrs:
            if attr not in kwargs:
                kwargs[attr] = defaultClass
        super().__init__(*args, **kwargs)
        self._engine = None

    def __repr__(self):
        return "<{} {} {}>".format(
            self.__class__.__name__, self.info.familyName, self.info.styleName
        )

    @property
    def binaryPath(self):
        if hasattr(self, "_binaryPath"):
            return self._binaryPath
        return None

    @property
    def engine(self):
        if _shaper and self._engine is None:
            self._engine = LayoutEngine(self)
        return self._engine

    @classmethod
    def new(cls):
        font = cls()
        font.info.unitsPerEm = 1000
        font.info.ascender = 750
        font.info.capHeight = 700
        font.info.xHeight = 500
        font.info.descender = -250

        defaultGlyphSet = settings.defaultGlyphSet()
        if defaultGlyphSet:
            glyphNames = None
            glyphSets = settings.readGlyphSets()
            if defaultGlyphSet in glyphSets:
                glyphNames = glyphSets[defaultGlyphSet]
            if glyphNames is not None:
                for name in glyphNames:
                    font.get(name, asTemplate=True)
        font.dirty = False

        app = QApplication.instance()
        data = dict(font=font)
        app.postNotification("newFontCreated", data)

        return font

    def get(self, name, **kwargs):
        return self._glyphSet.get(name, **kwargs)

    def extract(self, path):
        import extractor

        fileFormat = extractor.extractFormat(path)
        app = QApplication.instance()
        data = dict(font=self, format=fileFormat)
        app.postNotification("fontWillExtract", data)
        # don't bring on UndoManager just yet
        func = self.newGlyph
        try:
            self.newGlyph = types.MethodType(Font.newGlyph, self)
            extractor.extractUFO(path, self, fileFormat)
            for glyph in self:
                glyph.dirty = False
                glyph.undoManager = UndoManager(glyph)
        finally:
            self.newGlyph = func
        self.dirty = False
        self._binaryPath = path

    def save(
        self,
        path=None,
        formatVersion=None,
        removeUnreferencedImages=False,
        progressBar=None,
    ):
        app = QApplication.instance()
        data = dict(font=self, path=path or self.path)
        app.postNotification("fontWillSave", data)
        super().save(path, formatVersion, removeUnreferencedImages, progressBar)
        app.postNotification("fontSaved", data)

    def export(self, path, format="otf", compression=None, **kwargs):
        if format == "otf":
            func = compileOTF
        elif format == "ttf":
            func = compileTTF
        else:
            raise ValueError("unknown format: %s" % format)
        if compression is not None:
            invalid = compression - {"none", "woff", "woff2"}
            if invalid:
                raise ValueError(f"unknown compression format: {invalid}")
        # info attrs
        missingAttrs = []
        for attr in (
            "familyName",
            "styleName",
            "unitsPerEm",
            "ascender",
            "descender",
            "xHeight",
            "capHeight",
        ):
            if getattr(self.info, attr) is None:
                missingAttrs.append(attr)
        if missingAttrs:
            raise ValueError(
                "font info attributes required for export are "
                "missing: {}".format(" ".join(missingAttrs))
            )
        # go ahead
        app = QApplication.instance()
        data = dict(
            font=self, path=path, format=format, compression=compression, kwargs=kwargs
        )
        app.postNotification("fontWillExport", data)
        otf = func(self, **kwargs)
        if compression is None or "none" in compression:
            otf.save(path)
        if compression is not None:
            for header in compression:
                if header == "none":
                    continue
                otf.flavor = header
                otf.save(f"{path}.{header}")
        app.postNotification("fontExported", data)

    # sort descriptor

    def _get_sortDescriptor(self):
        # TODO: I'd use defcon sortDescriptor but there is no hard
        # standard for glyphList
        value = self.lib.get("com.typesupply.defcon.sortDescriptor", None)
        if value is not None:
            value = list(value)
        return value

    def _set_sortDescriptor(self, value):
        oldValue = self.lib.get("com.typesupply.defcon.sortDescriptor")
        if value is None or len(value) == 0:
            value = None
            if "com.typesupply.defcon.sortDescriptor" in self.lib:
                del self.lib["com.typesupply.defcon.sortDescriptor"]
        else:
            self.lib["com.typesupply.defcon.sortDescriptor"] = value
        self.postNotification(
            "Font.SortDescriptorChanged", data=dict(oldValue=oldValue, newValue=value)
        )

    sortDescriptor = property(
        _get_sortDescriptor, _set_sortDescriptor, doc="The defcon sort descriptor."
    )


class TLayer(Layer):
    def get(
        self,
        name,
        override=False,
        addUnicode=True,
        asTemplate=False,
        markColor=None,
        width=600,
    ):
        if not override:
            if name in self:
                # TODO: return the glyph here (change dependant code)
                return None
        if asTemplate:
            dirty = self.dirty
            self.disableNotifications(notification=self.changeNotificationName)
        glyph = self.newGlyph(name)
        if asTemplate:
            self.dirty = dirty
            self.enableNotifications(notification=self.changeNotificationName)
        if asTemplate:
            glyph.disableNotifications()
        glyph.width = width
        if addUnicode:
            glyph.autoUnicodes()
        glyph.template = asTemplate
        if asTemplate:
            glyph.dirty = False
            glyph.enableNotifications()
        glyph.markColor = markColor

        app = QApplication.instance()
        data = dict(glyph=glyph)
        app.postNotification("newGlyphCreated", data)

        return glyph

    def loadGlyph(self, name):
        glyph = super().loadGlyph(name)
        glyph.undoManager = UndoManager(glyph)
        return glyph

    def newGlyph(self, name):
        glyph = super().newGlyph(name)
        glyph.undoManager = UndoManager(glyph)
        return glyph

    def _glyphsReloadFilter(self, glyphNames):
        for glyphName in glyphNames:
            if glyphName in self and self[glyphName].template:
                continue
            if glyphName not in self._glyphSet:
                # TODO: blindy treating every KeyError as a "former"
                # template glyph isn't particularly elegant.
                glyph = self[glyphName]
                glyph.clear()
                glyph.template = True
                glyph.dirty = False
                continue
            yield glyphName

    def reloadGlyphs(self, glyphNames):
        super().reloadGlyphs(self._glyphsReloadFilter(glyphNames))

    def saveGlyph(self, glyph, glyphSet, saveAs=False):
        if not glyph.template:
            super().saveGlyph(glyph, glyphSet, saveAs)


class TGlyph(Glyph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._template = False

    def __repr__(self):
        return "<{} {} ({})>".format(
            self.__class__.__name__, self.name, self.layer.name
        )

    def beginUndoGroup(self, text=None):
        self._undoManager.beginUndoGroup(text)

    def endUndoGroup(self):
        self._undoManager.endUndoGroup()

    # observe anchor selection

    def beginSelfAnchorNotificationObservation(self, anchor):
        if anchor.dispatcher is None:
            return
        super().beginSelfAnchorNotificationObservation(anchor)
        anchor.addObserver(
            observer=self,
            methodName="_selectionChanged",
            notification="Anchor.SelectionChanged",
        )

    def endSelfAnchorNotificationObservation(self, anchor):
        if anchor.dispatcher is None:
            return
        anchor.removeObserver(observer=self, notification="Anchor.SelectionChanged")
        super().endSelfAnchorNotificationObservation(anchor)

    # observe component selection

    def beginSelfComponentNotificationObservation(self, component):
        if component.dispatcher is None:
            return
        super().beginSelfComponentNotificationObservation(component)
        component.addObserver(
            observer=self,
            methodName="_selectionChanged",
            notification="Component.SelectionChanged",
        )

    def endSelfComponentNotificationObservation(self, component):
        if component.dispatcher is None:
            return
        component.removeObserver(
            observer=self, notification="Component.SelectionChanged"
        )
        super().endSelfComponentNotificationObservation(component)

    # observe contours selection

    def selfNotificationCallback(self, notification):
        super().selfNotificationCallback(notification)
        if notification.name == "Glyph.Changed" and self.dirty:
            self.template = False

    def beginSelfContourNotificationObservation(self, contour):
        if contour.dispatcher is None:
            return
        super().beginSelfContourNotificationObservation(contour)
        contour.addObserver(
            observer=self,
            methodName="_selectionChanged",
            notification="Contour.SelectionChanged",
        )

    def endSelfContourNotificationObservation(self, contour):
        if contour.dispatcher is None:
            return
        contour.removeObserver(observer=self, notification="Contour.SelectionChanged")
        super().endSelfContourNotificationObservation(contour)

    def _selectionChanged(self, notification):
        if self.dispatcher is None:
            return
        self.postNotification(notification="Glyph.SelectionChanged")

    def _get_selected(self):
        for contour in self:
            if not contour.selected:
                return False
        return True

    def _set_selected(self, value):
        for contour in self:
            contour.selected = value

    selected = property(
        _get_selected,
        _set_selected,
        doc="The selected state of the contour. "
        "Selected state corresponds to all children points being selected."
        "Set selected state to select or unselect all points in the glyph.",
    )

    def _get_selection(self):
        selection = set()
        for contour in self:
            selection.update(contour.selection)
        return selection

    def _set_selection(self, selection):
        if selection == self.selection:
            return
        for contour in self:
            contour.selection = selection

    selection = property(
        _get_selection,
        _set_selection,
        doc="A list of children points that are selected.",
    )

    def _get_template(self):
        return self._template

    def _set_template(self, value):
        self._template = value

    template = property(
        _get_template,
        _set_template,
        doc="A boolean indicating whether the glyph is a template glyph.",
    )

    def _get_side1KerningGroup(self):
        font = self.font
        if font is None:
            return
        groups = font.groups
        return groups.side1GroupForGlyphName(self.name)

    side1KerningGroup = property(
        _get_side1KerningGroup, doc="The left side kerning group of the glyph."
    )

    def _get_side2KerningGroup(self):
        font = self.font
        if font is None:
            return
        groups = font.groups
        return groups.side2GroupForGlyphName(self.name)

    side2KerningGroup = property(
        _get_side2KerningGroup, doc="The right side kerning group of the glyph."
    )

    def autoUnicodes(self):
        app = QApplication.instance()
        if app.GL2UV is not None:
            GL2UV = app.GL2UV
        else:
            GL2UV = fontTools.agl.AGL2UV
        hexes = "ABCDEF0123456789"
        name = self.name
        if name in GL2UV:
            uni = GL2UV[name]
        elif (
            name.startswith("uni")
            and len(name) == 7
            and all(c in hexes for c in name[3:])
        ):
            uni = int(name[3:], 16)
        elif (
            name.startswith("u")
            and len(name) in (5, 7)
            and all(c in hexes for c in name[1:])
        ):
            uni = int(name[1:], 16)
        else:
            return
        self.unicodes = [uni]

    def rename(self, newName):
        if self.layerSet is not None:
            font = self.font
            oldName = self.name
            font.disableNotifications()
            for layer in self.layerSet:
                if oldName in layer:
                    glyph = layer[oldName]
                    glyph.name = newName
            font.enableNotifications()
        else:
            self.name = newName

    def hasOverlap(self):
        closed = []
        length = len(self)
        for contour in self:
            if contour.open:
                length -= 1
            else:
                closed.append(contour)
        glyph = self.__class__()
        union(closed, glyph.getPointPen())
        return len(glyph) != length

    def removeOverlap(self):
        open_, closed = [], []
        for contour in self:
            (open_ if contour.open else closed).append(contour)
        self.beginUndoGroup()
        self.clearContours()
        pointPen = self.getPointPen()
        union(closed, pointPen)
        for contour in open_:
            contour.drawPoints(pointPen)
        self.endUndoGroup()

    def scale(self, pt, center=(0, 0)):
        dx, dy = center
        x, y = pt
        sT = Identity.translate(dx, dy)
        sT = sT.scale(x=x, y=y)
        sT = sT.translate(-dx, -dy)
        self.transform(sT)

    def transform(self, matrix):
        self.beginUndoGroup()
        for contour in self:
            contour.transform(matrix)
        for component in self.components:
            component.transform(matrix)
        for anchor in self.anchors:
            anchor.transform(matrix)
        for guideline in self.guidelines:
            guideline.transform(matrix)
        self.endUndoGroup()

    def rotate(self, angle, offset=(0, 0)):
        dx, dy = offset
        radAngle = math.radians(angle)
        rT = Identity.translate(dx, dy)
        rT = rT.rotate(radAngle)
        rT = rT.translate(-dx, -dy)
        self.transform(rT)

    def skew(self, angle, offset=(0, 0)):
        dx, dy = offset
        x, y = angle
        x, y = math.radians(x), math.radians(y)
        sT = Identity.translate(dx, dy)
        sT = sT.skew(x, y)
        sT = sT.translate(-dx, -dy)
        self.transform(sT)

    def snap(self, base):
        self.beginUndoGroup()
        for contour in self:
            contour.snap(base)
        for component in self.components:
            component.snap(base)
        for anchor in self.anchors:
            anchor.snap(base)
        for guideline in self.guidelines:
            guideline.snap(base)
        self.endUndoGroup()


class TKerning(Kerning):
    def find(self, firstGlyph, secondGlyph):
        first = firstGlyph.name
        second = secondGlyph.name
        firstGroup = firstGlyph.side2KerningGroup
        secondGroup = secondGlyph.side1KerningGroup
        # make an ordered list of pairs to look up
        pairs = [
            (first, second),
            (first, secondGroup),
            (firstGroup, second),
            (firstGroup, secondGroup),
        ]
        # look up the pairs and return any matches
        for pair in pairs:
            if pair in self:
                return self[pair]
        return 0

    def write(self, firstGlyph, secondGlyph, value):
        first = firstGlyph.name
        second = secondGlyph.name
        firstGroup = firstGlyph.side2KerningGroup
        secondGroup = secondGlyph.side1KerningGroup
        pairs = [
            (first, second),
            (first, secondGroup),
            (firstGroup, second),
            (firstGroup, secondGroup),
        ]
        for pair in pairs:
            if pair in self:
                self[pair] = value
                return
        self[pairs[3 if firstGroup and secondGroup else 0]] = value


class TGroups(Groups):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _bootstrapGroupsCache(self):
        self._buildGroupsCache()
        # TODO: removeObserver
        self.addObserver(self, "_groupSet", "Groups.GroupSet")
        self.addObserver(self, "_groupDeleted", "Groups.GroupDeleted")
        self.addObserver(self, "_buildGroupsCache", "Groups.Cleared")
        self.addObserver(self, "_buildGroupsCache", "Groups.Updated")

    def _buildGroupsCache(self, *_):
        self._side1Groups = dict()
        self._side2Groups = dict()
        for group in self.keys():
            if group.startswith("public.kern1."):
                stor = self._side1Groups
            elif group.startswith("public.kern2."):
                stor = self._side2Groups
            else:
                continue
            for glyphName in self[group]:
                if glyphName is None:
                    continue
                stor[glyphName] = group

    def _groupSet(self, notification):
        group = notification.data["key"]
        if group.startswith("public.kern1."):
            stor = self._side1Groups
        elif group.startswith("public.kern2"):
            stor = self._side2Groups
        else:
            return
        oldValue = set(notification.data["oldValue"])
        value = set(notification.data["value"])
        for delName in oldValue - value:
            del stor[delName]
        for addName in value - oldValue:
            if addName is None:
                continue
            stor[addName] = group

    def _groupDeleted(self, notification):
        group = notification.data["key"]
        if not group.startswith("public.kern"):
            return
        for stor in (self._side1Groups, self._side2Groups):
            for glyphName, group_ in stor.items():
                if group_ == group:
                    del stor[glyphName]

    def side1GroupForGlyphName(self, glyphName):
        if not hasattr(self, "_side1Groups"):
            self._bootstrapGroupsCache()
        return self._side1Groups.get(glyphName)

    def side2GroupForGlyphName(self, glyphName):
        if not hasattr(self, "_side2Groups"):
            self._bootstrapGroupsCache()
        return self._side2Groups.get(glyphName)


class TContour(Contour):
    def __init__(self, *args, **kwargs):
        if "pointClass" not in kwargs:
            kwargs["pointClass"] = TPoint
        super().__init__(*args, **kwargs)

    def _get_selected(self):
        for point in self:
            if not point.selected:
                return False
        return True

    def _set_selected(self, value):
        for point in self:
            point.selected = value
        self.postNotification(notification="Contour.SelectionChanged")

    selected = property(
        _get_selected,
        _set_selected,
        doc="The selected state of the contour. "
        "Selected state corresponds to all children points being selected.",
    )

    def _get_selection(self):
        selection = set()
        for point in self:
            if point.selected:
                selection.add(point)
        return selection

    def _set_selection(self, selection):
        if selection == self.selection:
            return
        for point in self:
            point.selected = point in selection
        self.postNotification(notification="Contour.SelectionChanged")

    selection = property(
        _get_selection,
        _set_selection,
        doc="A list of children points that are selected.",
    )

    def drawPoints(self, pointPen):
        """
        Draw the contour with **pointPen**.
        """
        pointPen.beginPath()
        for point in self._points:
            pointPen.addPoint(
                (point.x, point.y),
                segmentType=point.segmentType,
                smooth=point.smooth,
                name=point.name,
                selected=point.selected,
            )
        pointPen.endPath()

    def getPoint(self, index):
        return self[index % len(self)]

    def scale(self, pt, center=(0, 0)):
        dx, dy = center
        x, y = pt
        sT = Identity.translate(dx, dy)
        sT = sT.scale(x, y)
        sT = sT.translate(-dx, -dy)
        self.transform(sT)

    def transform(self, matrix):
        for point in self:
            point.x, point.y = matrix.transformPoint((point.x, point.y))
        self.dirty = True

    def snap(self, base):
        for point in self:
            point.x = _snap(point.x, base)
            point.y = _snap(point.y, base)
        self.dirty = True


class TAnchor(Anchor):
    def __init__(self, *args, **kwargs):
        self._selected = False
        super().__init__(*args, **kwargs)
        if "anchorDict" in kwargs:
            anchorDict = kwargs["anchorDict"]
            if anchorDict is not None:
                self._selected = anchorDict.get("selected", False)

    def _get_selected(self):
        return self._selected

    def _set_selected(self, value):
        if value == self._selected:
            return
        self._selected = value
        self.postNotification(notification="Anchor.SelectionChanged")

    # TODO: add to repr
    selected = property(
        _get_selected,
        _set_selected,
        doc="A boolean indicating the selected state of the anchor.",
    )

    def scale(self, pt, center=(0, 0)):
        dx, dy = center
        x, y = pt
        sT = Identity.translate(dx, dy)
        sT = sT.scale(x, y)
        sT = sT.translate(-dx, -dy)
        self.transform(sT)

    def transform(self, matrix):
        self.x, self.y = matrix.transformPoint((self.x, self.y))

    def snap(self, base):
        self.x = _snap(self.x, base)
        self.y = _snap(self.y, base)


class TComponent(Component):
    def __init__(self, *args, **kwargs):
        self._selected = False
        super().__init__(*args, **kwargs)

    def _get_selected(self):
        return self._selected

    def _set_selected(self, value):
        if value == self._selected:
            return
        self._selected = value
        self.postNotification(notification="Component.SelectionChanged")

    selected = property(
        _get_selected,
        _set_selected,
        doc="A boolean indicating the selected state of the component.",
    )

    def scale(self, pt, center=(0, 0)):
        dx, dy = center
        x, y = pt
        sT = Identity.translate(dx, dy)
        sT = sT.scale(x, y)
        sT = sT.translate(-dx, -dy)
        self.transform(sT)

    def transform(self, matrix):
        self.transformation = tuple(matrix.transform(self.transformation))

    def snap(self, base):
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = self._transformation
        xOffset = _snap(xOffset, base)
        yOffset = _snap(yOffset, base)
        # TODO: should scale be snapped too?
        self.transformation = (xScale, xyScale, yxScale, yScale, xOffset, yOffset)


class TPoint(Point):
    __slots__ = ["_selected"]

    def __init__(self, pt, selected=False, **kwargs):
        super().__init__(pt, **kwargs)
        self._selected = selected

    def _get_selected(self):
        return self._selected

    def _set_selected(self, value):
        self._selected = value

    selected = property(
        _get_selected,
        _set_selected,
        doc="A boolean indicating the selected state of the point.",
    )


class TGuideline(Guideline):
    def __init__(self, *args, **kwargs):
        self._selected = False
        super().__init__(*args, **kwargs)
        if "guidelineDict" in kwargs:
            guidelineDict = kwargs["guidelineDict"]
            if guidelineDict is not None:
                self._selected = guidelineDict.get("selected", False)

    def _get_selected(self):
        return self._selected

    def _set_selected(self, value):
        if value == self._selected:
            return
        self._selected = value
        self.postNotification(notification="Guideline.SelectionChanged")

    # TODO: add to repr
    selected = property(
        _get_selected,
        _set_selected,
        doc="A boolean indicating the selected state of the guideline.",
    )

    def scale(self, pt, center=(0, 0)):
        dx, dy = center
        x, y = pt
        sT = Identity.translate(dx, dy)
        sT = sT.scale(x, y)
        sT = sT.translate(-dx, -dy)
        self.transform(sT)

    def transform(self, matrix):
        self.x, self.y = matrix.transformPoint((self.x, self.y))

    def snap(self, base):
        self.x = _snap(self.x, base)
        self.y = _snap(self.y, base)


class TImage(Image):
    def __init__(self, *args, **kwargs):
        self._selected = False
        super().__init__(*args, **kwargs)
        if "imageDict" in kwargs:
            imageDict = kwargs["imageDict"]
            if imageDict is not None:
                self._selected = imageDict.get("selected", False)

    def _get_selected(self):
        return self._selected

    def _set_selected(self, value):
        if value == self._selected:
            return
        self._selected = value
        self.postNotification(notification="Image.SelectionChanged")

    selected = property(
        _get_selected,
        _set_selected,
        doc="A boolean indicating the selected state of the anchor.",
    )


def _snap(x, base=5):
    if not base:
        return x
    return base * round(x / base)
