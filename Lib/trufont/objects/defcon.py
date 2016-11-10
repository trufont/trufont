from booleanOperations.booleanGlyph import BooleanGlyph
from defcon import (
    Font, Layer, Glyph, Groups, Kerning, Contour, Point, Anchor, Component,
    Guideline, Image)
from defcon.objects.base import BaseObject
from fontTools.misc.transform import Identity
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication
from trufont.objects import settings
import fontTools
import math


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

    @property
    def binaryPath(self):
        if hasattr(self, "_binaryPath"):
            return self._binaryPath
        return None

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
        data = dict(
            font=self,
            format=fileFormat,
        )
        app.postNotification("fontWillExtract", data)
        extractor.extractUFO(path, self, fileFormat)
        for glyph in self:
            glyph.dirty = False
        self.dirty = False
        self._binaryPath = path

    def save(self, path=None, formatVersion=None,
             removeUnreferencedImages=False, progressBar=None):
        app = QApplication.instance()
        data = dict(
            font=self,
            path=path or self.path,
        )
        app.postNotification("fontWillSave", data)
        super().save(
            path, formatVersion, removeUnreferencedImages, progressBar)
        for glyph in self:
            glyph.dirty = False
        self.dirty = False
        app.postNotification("fontSaved", data)

    def export(self, path, format="otf"):
        if format not in ("otf", "ttf"):
            raise ValueError("unknown format: %s")
        missingAttrs = []
        for attr in ("familyName", "styleName", "unitsPerEm", "ascender",
                     "descender", "xHeight", "capHeight"):
            if getattr(self.info, attr) is None:
                missingAttrs.append(attr)
        if missingAttrs:
            raise ValueError("font info attributes required for export are "
                             "missing: {}".format(" ".join(missingAttrs)))
        # go ahead
        app = QApplication.instance()
        data = dict(
            font=self,
            format=format,
            path=path,
        )
        rp = "TruFont.QuadraticTTFont" if format == "ttf" else "TruFont.TTFont"
        app.postNotification("fontWillExport", data)
        otf = self.getRepresentation(rp)
        otf.save(path)
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
        if oldValue == value:
            return
        if value is None or len(value) == 0:
            value = None
            if "com.typesupply.defcon.sortDescriptor" in self.lib:
                del self.lib["com.typesupply.defcon.sortDescriptor"]
        else:
            self.lib["com.typesupply.defcon.sortDescriptor"] = value
        self.postNotification("Font.SortDescriptorChanged",
                              data=dict(oldValue=oldValue, newValue=value))

    sortDescriptor = property(_get_sortDescriptor, _set_sortDescriptor,
                              doc="The defcon sort descriptor.")


class TLayer(Layer):

    def get(self, name, override=False, addUnicode=True, asTemplate=False,
            markColor=None, width=600):
        if not override:
            if name in self:
                # TODO: return the glyph here (change dependant code)
                return None
        glyph = self.newGlyph(name)
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

    def saveGlyph(self, glyph, glyphSet, saveAs=False):
        if not glyph.template:
            super().saveGlyph(glyph, glyphSet, saveAs)


class TGlyph(Glyph):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._template = False
        self._undoManager = UndoManager(self)

    # observe anchor selection

    def beginSelfAnchorNotificationObservation(self, anchor):
        if anchor.dispatcher is None:
            return
        super().beginSelfAnchorNotificationObservation(anchor)
        anchor.addObserver(
            observer=self, methodName="_selectionChanged",
            notification="Anchor.SelectionChanged")

    def endSelfAnchorNotificationObservation(self, anchor):
        if anchor.dispatcher is None:
            return
        anchor.removeObserver(
            observer=self, notification="Anchor.SelectionChanged")
        super().endSelfAnchorNotificationObservation(anchor)

    # observe component selection

    def beginSelfComponentNotificationObservation(self, component):
        if component.dispatcher is None:
            return
        super().beginSelfComponentNotificationObservation(component)
        component.addObserver(
            observer=self, methodName="_selectionChanged",
            notification="Component.SelectionChanged")

    def endSelfComponentNotificationObservation(self, component):
        if component.dispatcher is None:
            return
        component.removeObserver(
            observer=self, notification="Component.SelectionChanged")
        super().endSelfComponentNotificationObservation(component)

    # observe contours selection

    def beginSelfContourNotificationObservation(self, contour):
        if contour.dispatcher is None:
            return
        super().beginSelfContourNotificationObservation(contour)
        contour.addObserver(
            observer=self, methodName="_selectionChanged",
            notification="Contour.SelectionChanged")

    def endSelfContourNotificationObservation(self, contour):
        if contour.dispatcher is None:
            return
        contour.removeObserver(
            observer=self, notification="Contour.SelectionChanged")
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
        _get_selected, _set_selected, doc="The selected state of the contour. "
        "Selected state corresponds to all children points being selected."
        "Set selected state to select or unselect all points in the glyph.")

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

    selection = property(_get_selection, _set_selection,
                         doc="A list of children points that are selected.")

    def _get_template(self):
        return self._template

    def _set_template(self, value):
        self._template = value

    template = property(
        _get_template, _set_template,
        doc="A boolean indicating whether the glyph is a template glyph.")

    def _set_dirty(self, value):
        BaseObject._set_dirty(self, value)
        if value:
            self.template = False

    dirty = property(BaseObject._get_dirty, _set_dirty)

    def _get_side1KerningGroup(self):
        font = self.font
        if font is None:
            return
        groups = font.groups
        return groups.side1GroupForGlyphName(self.name)

    side1KerningGroup = property(
        _get_side1KerningGroup,
        doc="The left side kerning group of the glyph.")

    def _get_side2KerningGroup(self):
        font = self.font
        if font is None:
            return
        groups = font.groups
        return groups.side2GroupForGlyphName(self.name)

    side2KerningGroup = property(
        _get_side2KerningGroup,
        doc="The right side kerning group of the glyph.")

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
        elif (name.startswith("uni") and len(name) == 7 and
              all(c in hexes for c in name[3:])):
            uni = int(name[3:], 16)
        elif (name.startswith("u") and len(name) in (5, 7) and
              all(c in hexes for c in name[1:])):
            uni = int(name[1:], 16)
        else:
            return
        self.unicodes = [uni]

    def hasOverlap(self):
        bGlyph = BooleanGlyph()
        pen = bGlyph.getPointPen()
        openContours = 0
        for contour in self:
            if not contour.open:
                contour.drawPoints(pen)
            else:
                openContours += 1
        bGlyph.removeOverlap()
        return len(bGlyph.contours) + openContours != len(self)

    def removeOverlap(self):
        # TODO: maybe clear undo stack if no changes
        self.prepareUndo()
        bGlyph = BooleanGlyph()
        pen = bGlyph.getPointPen()
        for contour in list(self):
            if not contour.open:
                contour.drawPoints(pen)
                self.removeContour(contour)
            else:
                contour.selected = False
        bGlyph = bGlyph.removeOverlap()
        pen = self.getPointPen()
        for contour in bGlyph.contours:
            contour.drawPoints(pen)

        self.dirty = True

    def scale(self, pt, center=(0, 0)):
        for contour in self:
            contour.scale(pt, center=center)
        for component in self.components:
            component.scale(pt, center=center)
        for anchor in self.anchors:
            anchor.scale(pt, center=center)

    def transform(self, matrix):
        for contour in self:
            contour.transform(matrix)
        for anchor in self.anchors:
            anchor.transform(matrix)

    def rotate(self, angle, offset=(0, 0)):
        radAngle = math.radians(angle)
        rT = Identity.translate(offset[0], offset[1])
        rT = rT.rotate(radAngle)
        rT = rT.translate(-offset[0], -offset[1])
        self.transform(rT)

    def skew(self, angle, offset=(0, 0)):
        xRad = math.radians(angle[0])
        yRad = math.radians(angle[1])
        rT = Identity.translate(offset[0], offset[1])
        rT = rT.skew(xRad, yRad)
        self.transform(rT)

    def snap(self, base):
        for contour in self:
            contour.snap(base)
        for component in self.components:
            component.snap(base)
        for anchor in self.anchors:
            anchor.snap(base)


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
            (firstGroup, secondGroup)
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
            (firstGroup, secondGroup)
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
        _get_selected, _set_selected, doc="The selected state of the contour. "
        "Selected state corresponds to all children points being selected.")

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

    selection = property(_get_selection, _set_selection,
                         doc="A list of children points that are selected.")

    def drawPoints(self, pointPen):
        """
        Draw the contour with **pointPen**.
        """
        pointPen.beginPath()
        for point in self._points:
            pointPen.addPoint((point.x, point.y),
                              segmentType=point.segmentType,
                              smooth=point.smooth, name=point.name,
                              selected=point.selected)
        pointPen.endPath()

    def getPoint(self, index):
        return self[index % len(self)]

    def scale(self, pt, center=(0, 0)):
        for point in self:
            point.x, point.y = _scalePointFromCenter(
                (point.x, point.y), pt, center)
        self.dirty = True

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
        _get_selected, _set_selected,
        doc="A boolean indicating the selected state of the anchor.")

    def scale(self, pt, center=(0, 0)):
        self.x, self.y = _scalePointFromCenter(
            (self.x, self.y), pt, center)

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
        _get_selected, _set_selected,
        doc="A boolean indicating the selected state of the component.")

    def scale(self, pt, center=(0, 0)):
        x, y = pt
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = \
            self._transformation
        xOffset, yOffset = _scalePointFromCenter(
            (xOffset, yOffset), pt, center)
        xScale, yScale = xScale * x, yScale * y
        self.transformation = (
            xScale, xyScale, yxScale, yScale, xOffset, yOffset)

    def snap(self, base):
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = \
            self._transformation
        xOffset = _snap(xOffset, base)
        yOffset = _snap(yOffset, base)
        # TODO: should scale be snapped too?
        self.transformation = (
            xScale, xyScale, yxScale, yScale, xOffset, yOffset)


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
        _get_selected, _set_selected,
        doc="A boolean indicating the selected state of the point.")


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
        _get_selected, _set_selected,
        doc="A boolean indicating the selected state of the guideline.")


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
        _get_selected, _set_selected,
        doc="A boolean indicating the selected state of the anchor.")


class UndoManager(QObject):
    canUndoChanged = pyqtSignal(bool)
    canRedoChanged = pyqtSignal(bool)

    def __init__(self, parent):
        super().__init__()
        self._undoStack = []
        self._redoStack = []
        self._parent = parent
        self._shouldBackupCurrent = False

    def prepareTarget(self, title=None):
        data = self._parent.serialize()
        undoWasLocked = not self.canUndo()
        redoWasEnabled = self.canRedo()
        # prune eventual redo and add push state
        self._redoStack = []
        self._undoStack.append((data, title))
        # set ptr to current state
        self._shouldBackupCurrent = True
        if undoWasLocked:
            self.canUndoChanged.emit(True)
        if redoWasEnabled:
            self.canRedoChanged.emit(False)

    def canUndo(self):
        return bool(len(self._undoStack))

    def getUndoTitle(self, index):
        data = self._undoStack[index]
        return data[1]

    def undo(self, index):
        data = self._undoStack[index]
        redoWasLocked = not self.canRedo()
        if self._shouldBackupCurrent:
            forwardData = self._parent.serialize()
            self._redoStack.append((forwardData, None))
        self._parent.deserialize(data[0])
        self._redoStack = self._undoStack[index:] + self._redoStack
        self._undoStack = self._undoStack[:index]
        self._shouldBackupCurrent = False
        if redoWasLocked:
            self.canRedoChanged.emit(True)
        if not self.canUndo():
            self.canUndoChanged.emit(False)

    def canRedo(self):
        return bool(len(self._redoStack))

    def getRedoTitle(self, index):
        data = self._redoStack[index]
        return data[1]

    def redo(self, index):
        data = self._redoStack[index]
        undoWasLocked = not self.canUndo()
        self._parent.deserialize(data[0])
        self._undoStack = self._undoStack + self._redoStack[:index+1]
        if index + 1 < len(self._redoStack):
            self._redoStack = self._redoStack[index+1:]
        else:
            self._redoStack = []
        if undoWasLocked:
            self.canUndoChanged.emit(True)
        if not self.canRedo():
            self.canRedoChanged.emit(False)


def _scalePointFromCenter(point, scale, center):
    pointX, pointY = point
    scaleX, scaleY = scale
    centerX, centerY = center
    ogCenter = (centerX, centerY)
    scaledCenter = (centerX * scaleX, centerY * scaleY)
    shiftVal = (scaledCenter[0] - ogCenter[0], scaledCenter[1] - ogCenter[1])
    scaledPointX = (pointX * scaleX) - shiftVal[0]
    scaledPointY = (pointY * scaleY) - shiftVal[1]
    return (scaledPointX, scaledPointY)


def _snap(x, base=5):
    if not base:
        return x
    return base * round(x / base)
