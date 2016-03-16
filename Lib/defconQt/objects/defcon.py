from booleanOperations.booleanGlyph import BooleanGlyph
from defcon import Font, Contour, Glyph, Layer, Anchor, Component, Point
from defcon.objects.base import BaseObject
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication
import fontTools


class TFont(Font):

    def __init__(self, *args, **kwargs):
        # TODO: maybe subclass all objects into our own for caller stability
        attrs = (
            ("glyphAnchorClass", TAnchor),
            ("glyphComponentClass", TComponent),
            ("glyphClass", TGlyph),
            ("glyphContourClass", TContour),
            ("glyphPointClass", TPoint),
            ("layerClass", TLayer)
        )
        for attr, defaultClass in attrs:
            if attr not in kwargs:
                kwargs[attr] = defaultClass
        super().__init__(*args, **kwargs)

    # TODO: maybe take this out of the class
    def newStandardGlyph(self, name, override=False, addUnicode=True,
                         asTemplate=False, markColor=None, width=500):
        if not override:
            if name in self:
                return None
        glyph = self.newGlyph(name)
        glyph.width = width
        if addUnicode:
            glyph.autoUnicodes()
        glyph.template = asTemplate
        glyph.markColor = markColor
        return glyph


class TLayer(Layer):

    def saveGlyph(self, glyph, glyphSet, saveAs=False):
        if not glyph.template:
            super().saveGlyph(glyph, glyphSet, saveAs)


class TGlyph(Glyph):

    def __init__(self, *args, **kwargs):
        super(TGlyph, self).__init__(*args, **kwargs)
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


class TContour(Contour):

    def __init__(self, *args, **kwargs):
        if not "pointClass" in kwargs:
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


class TAnchor(Anchor):
    def __init__(self, *args, **kwargs):
        self._selected = False
        super(TAnchor, self).__init__(*args, **kwargs)
        if "anchorDict" in kwargs:
            anchorDict = kwargs["anchorDict"]
        else:
            anchorDict = None
        if anchorDict is not None:
            self._selected = anchorDict.get("selected")

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


class TComponent(Component):
    def __init__(self, *args, **kwargs):
        self._selected = False
        super(TComponent, self).__init__(*args, **kwargs)

    def _get_selected(self):
        return self._selected

    def _set_selected(self, value):
        if value == self._selected:
            return
        self._selected = value
        self.postNotification(notification="Component.SelectionChanged")

    # TODO: add to repr
    selected = property(
        _get_selected, _set_selected,
        doc="A boolean indicating the selected state of the component.")


class TPoint(Point):
    __slots__ = ["_selected"]

    def __init__(self, pt, selected=False, **kwargs):
        super(TPoint, self).__init__(pt, **kwargs)
        self._selected = selected

    def _get_selected(self):
        return self._selected

    def _set_selected(self, value):
        self._selected = value

    # TODO: add to repr
    selected = property(
        _get_selected, _set_selected,
        doc="A boolean indicating the selected state of the point.")


class GlyphSet(object):
    __slots__ = ["_name", "_glyphNames"]

    def __init__(self, glyphNames, name):
        self._name = str(name)
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

    glyphNames = property(_get_glyphNames, _set_glyphNames,
                          doc="List of glyph names.")


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
