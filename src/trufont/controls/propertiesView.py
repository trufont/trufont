import math
import pathops
import trufont
from trufont.controls.alignmentControl import AlignmentControl
from trufont.controls.layersView import LayersView
from trufont.controls.spinCtrl import SpinCtrl
from trufont.util import platformSpecific
from trufont.util.drawing import CreatePath, cos_sin_deg
from trufont.util.pathops import PathPen

from tfont.objects import Point, Transformation, Layer, Path

import wx
from wx import GetTranslation as tr

import logging
from trufont.objects.truglyph import TruGlyph
from typing import Any, Collection, Tuple, List, Dict, Callable

import trufont.objects.undoredomgr as undoredomgr
import trufont.util.func_copy as func_copy

from tfont.converters.tfontConverter import TFontConverter
TFONT_CONV = TFontConverter(indent=None)
TFONT_CONVU = TFontConverter()

import trufont.util.deco4class as deco4class

path = CreatePath()
path.MoveToPoint(12.0, 9.0)
path.AddLineToPoint(9.0, 9.0)
path.AddLineToPoint(9.0, 12.0)
path.AddCurveToPoint(9.0, 12.549, 8.549, 13.0, 8.0, 13.0)
path.AddCurveToPoint(7.451, 13.0, 7.0, 12.549, 7.0, 12.0)
path.AddLineToPoint(7.0, 9.0)
path.AddLineToPoint(4.0, 9.0)
path.AddCurveToPoint(3.451, 9.0, 3.0, 8.549, 3.0, 8.0)
path.AddCurveToPoint(3.0, 7.451, 3.451, 7.0, 4.0, 7.0)
path.AddLineToPoint(7.0, 7.0)
path.AddLineToPoint(7.0, 4.0)
path.AddCurveToPoint(7.0, 3.451, 7.451, 3.0, 8.0, 3.0)
path.AddCurveToPoint(8.549, 3.0, 9.0, 3.451, 9.0, 4.0)
path.AddLineToPoint(9.0, 7.0)
path.AddLineToPoint(12.0, 7.0)
path.AddCurveToPoint(12.549, 7.0, 13.0, 7.451, 13.0, 8.0)
path.CloseSubpath()


#-------------------------
# Used by undoredo decorator
#-------------------------
def align_expand_params(layer: Layer, tglyph: TruGlyph, operation: str):
    """Used with align functions -  Nothing to """
    return layer    

@undoredomgr.layer_decorate_undoredo(align_expand_params, operation="Align Horiz Left", 
                                     paths=True, guidelines=False, components=False, anchors=False)
def _alignHLeft(layer: Layer, tglyph: TruGlyph, operation: str):
    selectedPaths = []
    xMin_all = None
    for path in layer._paths:
        if any(pt.selected for pt in path._points):
            selectedPaths.append(path)
            xMin = path.bounds[0]
            if xMin_all is None or xMin_all > xMin:
                xMin_all = xMin
    if not selectedPaths:
        return

    # modify selected paths 
    for path in selectedPaths:
        xMin = path.bounds[0]
        if xMin > xMin_all:
            delta = xMin_all - xMin
            path.transform(Transformation(xOffset=delta))

@undoredomgr.layer_decorate_undoredo(align_expand_params, operation="Align Horiz Center", 
                                     paths=True, guidelines=False, components=False, anchors=False)
def _alignHCenter(layer: Layer, tglyph: TruGlyph, operation: str):
    selectedPaths = []
    xMin_all, xMax_all = None, None
    for path in layer._paths:
        if any(pt.selected for pt in path._points):
            selectedPaths.append(path)
            xMin, _, xMax, _ = path.bounds
            if xMin_all is None or xMin_all > xMin:
                xMin_all = xMin
            if xMax_all is None or xMax_all < xMax:
                xMax_all = xMax
    if not selectedPaths:
        return

    # modify selected paths 
    xAvg_all = xMin_all + round(.5 * (xMax_all - xMin_all))
    for path in selectedPaths:
        xMin, _, xMax, _ = path.bounds
        xAvg = xMin + round(.5 * (xMax - xMin))
        if xAvg != xAvg_all:
            delta = xAvg_all - xAvg
            path.transform(Transformation(xOffset=delta))


@undoredomgr.layer_decorate_undoredo(align_expand_params, operation="Align Horiz Right", 
                                     paths=True, guidelines=False, components=False, anchors=False)
def _alignHRight(layer: Layer, tglyph: TruGlyph, operation: str):
    selectedPaths = []
    xMax_all = None
    for path in layer._paths:
        if any(pt.selected for pt in path._points):
            xMax = path.bounds[2]
            selectedPaths.append(path)
            if xMax_all is None or xMax_all < xMax:
                xMax_all = xMax
    if not selectedPaths:
        return

    # modify selected paths 
    for path in selectedPaths:
        xMax = path.bounds[2]
        if xMax < xMax_all:
            delta = xMax_all - xMax
            path.transform(Transformation(xOffset=delta))


@undoredomgr.layer_decorate_undoredo(align_expand_params, operation="Align Vert Top", 
                                     paths=True, guidelines=False, components=False, anchors=False)
def _alignVTop(layer: Layer, tglyph: TruGlyph, operation: str):
    selectedPaths = []
    yMax_all = None
    for path in layer._paths:
        if any(pt.selected for pt in path._points):
            selectedPaths.append(path)
            yMax = path.bounds[3]
            if yMax_all is None or yMax_all < yMax:
                yMax_all = yMax
    if not selectedPaths:
        return

    # modify selected paths 
    for path in selectedPaths:
        yMax = path.bounds[3]
        if yMax < yMax_all:
            delta = yMax_all - yMax
            path.transform(Transformation(yOffset=delta))

@undoredomgr.layer_decorate_undoredo(align_expand_params, operation="Align Vert Center", 
                                     paths=True, guidelines=False, components=False, anchors=False)
def _alignVCenter(layer: Layer, tglyph: TruGlyph, operation: str):
    selectedPaths = []
    yMin_all, yMax_all = None, None
    for path in layer._paths:
        if any(pt.selected for pt in path._points):
            selectedPaths.append(path)
            _, yMin, _, yMax = path.bounds
            if yMin_all is None or yMin_all > yMin:
                yMin_all = yMin
            if yMax_all is None or yMax_all < yMax:
                yMax_all = yMax
    if not selectedPaths:
        return

    # modify selected paths 
    yAvg_all = yMin_all + round(.5 * (yMax_all - yMin_all))
    for path in selectedPaths:
        _, yMin, _, yMax = path.bounds
        yAvg = yMin + round(.5 * (yMax - yMin))
        if yAvg != yAvg_all:
            delta = yAvg_all - yAvg
            path.transform(Transformation(yOffset=delta))


@undoredomgr.layer_decorate_undoredo(align_expand_params, operation="Align Vert Bottom", 
                                     paths=True, guidelines=False, components=False, anchors=False)
def _alignVBottom(layer: Layer, tglyph: TruGlyph, operation: str):
    selectedPaths = []
    yMin_all = None
    for path in layer._paths:
        if any(pt.selected for pt in path._points):
            selectedPaths.append(path)
            yMin = path.bounds[1]
            if yMin_all is None or yMin_all > yMin:
                yMin_all = yMin
    if not selectedPaths:
        return

    # modify selected paths 
    for path in selectedPaths:
        yMin = path.bounds[1]
        if yMin > yMin_all:
            delta = yMin_all - yMin
            path.transform(Transformation(yOffset=delta))


def makePropertiesLayout(parent, font):
    sizer = wx.BoxSizer(wx.VERTICAL)
    alignmentBar = ButtonBar(parent)
    btns = []
    path = CreatePath()
    path.MoveToPoint(13.961, 13.0)
    path.AddLineToPoint(5.039, 13.0)
    path.AddCurveToPoint(4.48, 13.009, 4.012, 12.559, 4.0, 12.0)
    path.AddLineToPoint(4.0, 10.0)
    path.AddCurveToPoint(4.012, 9.441, 4.48, 8.991, 5.039, 9.0)
    path.AddLineToPoint(13.962, 9.0)
    path.AddCurveToPoint(14.521, 8.991, 14.989, 9.441, 15.001, 10.0)
    path.AddLineToPoint(15.001, 12.0)
    path.CloseSubpath()
    path.MoveToPoint(9.951, 7.0)
    path.AddLineToPoint(5.039, 7.0)
    path.AddCurveToPoint(4.48, 7.009, 4.012, 6.559, 4.0, 6.0)
    path.AddLineToPoint(4.0, 4.0)
    path.AddCurveToPoint(4.012, 3.441, 4.48, 2.991, 5.039, 3.0)
    path.AddLineToPoint(9.951, 3.0)
    path.AddCurveToPoint(10.51, 2.991, 10.978, 3.441, 10.99, 4.0)
    path.AddLineToPoint(10.99, 6.0)
    path.CloseSubpath()
    path.MoveToPoint(2.0, 0.5)
    path.AddCurveToPoint(2.0, 0.224, 1.776, 0.0, 1.5, 0.0)
    path.AddCurveToPoint(1.224, 0.0, 1.0, 0.224, 1.0, 0.5)
    path.AddLineToPoint(1.0, 15.5)
    path.AddCurveToPoint(1.0, 15.776, 1.224, 16.0, 1.5, 16.0)
    path.AddCurveToPoint(1.776, 16.0, 2.0, 15.776, 2.0, 15.5)
    path.CloseSubpath()
    btns.append(Button(path, _alignHLeft, tr("Push selection left")))
    path = CreatePath()
    path.MoveToPoint(7.0, 3.0)
    path.AddLineToPoint(7.0, 0.5)
    path.AddCurveToPoint(7.0, 0.224, 7.224, 0.0, 7.5, 0.0)
    path.AddCurveToPoint(7.776, 0.0, 8.0, 0.224, 8.0, 0.5)
    path.AddLineToPoint(8.0, 3.0)
    path.AddLineToPoint(9.954, 3.0)
    path.AddCurveToPoint(10.514, 2.989, 10.985, 3.44, 10.999, 4.0)
    path.AddLineToPoint(10.999, 6.0)
    path.AddCurveToPoint(10.985, 6.56, 10.514, 7.011, 9.954, 7.0)
    path.AddLineToPoint(8.0, 7.0)
    path.AddLineToPoint(8.0, 9.0)
    path.AddLineToPoint(11.953, 9.0)
    path.AddCurveToPoint(12.514, 8.989, 12.985, 9.439, 13.0, 10.0)
    path.AddLineToPoint(13.0, 12.0)
    path.AddCurveToPoint(12.985, 12.563, 12.511, 13.014, 11.948, 13.0)
    path.AddLineToPoint(8.0, 13.0)
    path.AddLineToPoint(8.0, 15.5)
    path.AddCurveToPoint(8.0, 15.776, 7.776, 16.0, 7.5, 16.0)
    path.AddCurveToPoint(7.224, 16.0, 7.0, 15.776, 7.0, 15.5)
    path.AddLineToPoint(7.0, 13.0)
    path.AddLineToPoint(3.048, 13.0)
    path.AddCurveToPoint(2.487, 13.012, 2.015, 12.561, 2.0, 12.0)
    path.AddLineToPoint(2.0, 10.0)
    path.AddCurveToPoint(2.015, 9.439, 2.487, 8.988, 3.048, 9.0)
    path.AddLineToPoint(7.0, 9.0)
    path.AddLineToPoint(7.0, 7.0)
    path.AddLineToPoint(5.044, 7.0)
    path.AddCurveToPoint(4.484, 7.011, 4.013, 6.56, 3.999, 6.0)
    path.AddLineToPoint(3.999, 4.0)
    path.AddCurveToPoint(4.013, 3.44, 4.484, 2.989, 5.044, 3.0)
    path.CloseSubpath()
    btns.append(Button(path, _alignHCenter, tr("Push selection to hz. center")))
    path = CreatePath()
    path.MoveToPoint(10.958, 13.0)
    path.AddLineToPoint(2.042, 13.0)
    path.AddCurveToPoint(1.482, 13.01, 1.013, 12.559, 1.0, 12.0)
    path.AddLineToPoint(1.0, 10.0)
    path.AddCurveToPoint(1.013, 9.441, 1.482, 8.99, 2.042, 9.0)
    path.AddLineToPoint(10.959, 9.0)
    path.AddCurveToPoint(11.518, 8.991, 11.987, 9.441, 12.0, 10.0)
    path.AddLineToPoint(12.0, 12.0)
    path.CloseSubpath()
    path.MoveToPoint(10.958, 7.0)
    path.AddLineToPoint(6.032, 7.0)
    path.AddCurveToPoint(5.472, 7.01, 5.003, 6.559, 4.99, 6.0)
    path.AddLineToPoint(4.99, 4.0)
    path.AddCurveToPoint(5.003, 3.441, 5.472, 2.99, 6.032, 3.0)
    path.AddLineToPoint(10.959, 3.0)
    path.AddCurveToPoint(11.518, 2.991, 11.987, 3.441, 12.0, 4.0)
    path.AddLineToPoint(12.0, 6.0)
    path.CloseSubpath()
    path.MoveToPoint(15.0, 0.5)
    path.AddCurveToPoint(15.0, 0.224, 14.776, 0.0, 14.5, 0.0)
    path.AddCurveToPoint(14.224, 0.0, 14.0, 0.224, 14.0, 0.5)
    path.AddLineToPoint(14.0, 15.5)
    path.AddCurveToPoint(14.0, 15.776, 14.224, 16.0, 14.5, 16.0)
    path.AddCurveToPoint(14.776, 16.0, 15.0, 15.776, 15.0, 15.5)
    path.CloseSubpath()
    btns.append(Button(path, _alignHRight, tr("Push selection right")))
    path = CreatePath()
    path.MoveToPoint(4.0, 3.978)
    path.AddLineToPoint(6.0, 3.978)
    path.AddCurveToPoint(6.559, 3.991, 7.009, 4.459, 7.0, 5.018)
    path.AddLineToPoint(7.0, 13.951)
    path.AddCurveToPoint(7.009, 14.51, 6.559, 14.978, 6.0, 14.991)
    path.AddLineToPoint(4.0, 14.991)
    path.AddCurveToPoint(3.441, 14.978, 2.991, 14.51, 3.0, 13.951)
    path.AddLineToPoint(3.0, 5.018)
    path.CloseSubpath()
    path.MoveToPoint(10.0, 3.993)
    path.AddLineToPoint(12.0, 3.993)
    path.AddCurveToPoint(12.559, 4.006, 13.009, 4.474, 13.0, 5.033)
    path.AddLineToPoint(13.0, 9.951)
    path.AddCurveToPoint(13.009, 10.51, 12.559, 10.978, 12.0, 10.991)
    path.AddLineToPoint(10.0, 10.991)
    path.AddCurveToPoint(9.441, 10.978, 8.991, 10.51, 9.0, 9.951)
    path.AddLineToPoint(9.0, 5.033)
    path.CloseSubpath()
    path.MoveToPoint(16.0, 1.5)
    path.AddCurveToPoint(16.0, 1.224, 15.776, 1.0, 15.5, 1.0)
    path.AddLineToPoint(0.5, 1.0)
    path.AddCurveToPoint(0.224, 1.0, 0.0, 1.224, 0.0, 1.5)
    path.AddCurveToPoint(0.0, 1.776, 0.224, 2.0, 0.5, 2.0)
    path.AddLineToPoint(15.5, 2.0)
    path.CloseSubpath()
    btns.append(Button(path, _alignVTop, tr("Push selection top")))
    path = CreatePath()
    path.MoveToPoint(7.0, 8.0)
    path.AddLineToPoint(7.0, 11.956)
    path.AddCurveToPoint(7.01, 12.516, 6.56, 12.986, 6.0, 13.0)
    path.AddLineToPoint(4.0, 13.0)
    path.AddCurveToPoint(3.44, 12.986, 2.99, 12.516, 3.0, 11.956)
    path.AddLineToPoint(3.0, 8.0)
    path.AddLineToPoint(0.5, 8.0)
    path.AddCurveToPoint(0.224, 8.0, 0.0, 7.776, 0.0, 7.5)
    path.AddCurveToPoint(0.0, 7.224, 0.224, 7.0, 0.5, 7.0)
    path.AddLineToPoint(3.0, 7.0)
    path.AddLineToPoint(3.0, 3.045)
    path.AddCurveToPoint(2.99, 2.485, 3.44, 2.015, 4.0, 2.0)
    path.AddLineToPoint(6.0, 2.0)
    path.AddCurveToPoint(6.56, 2.015, 7.01, 2.485, 7.0, 3.045)
    path.AddLineToPoint(7.0, 7.0)
    path.AddLineToPoint(9.0, 7.0)
    path.AddLineToPoint(9.0, 5.048)
    path.AddCurveToPoint(8.989, 4.487, 9.439, 4.015, 10.0, 4.0)
    path.AddLineToPoint(12.0, 4.0)
    path.AddCurveToPoint(12.561, 4.015, 13.011, 4.487, 13.0, 5.048)
    path.AddLineToPoint(13.0, 7.0)
    path.AddLineToPoint(15.5, 7.0)
    path.AddCurveToPoint(15.776, 7.0, 16.0, 7.224, 16.0, 7.5)
    path.AddCurveToPoint(16.0, 7.776, 15.776, 8.0, 15.5, 8.0)
    path.AddLineToPoint(13.0, 8.0)
    path.AddLineToPoint(13.0, 9.996)
    path.AddCurveToPoint(13.0, 10.0, 13.0, 10.003, 13.0, 10.007)
    path.AddCurveToPoint(13.0, 10.55, 12.554, 10.996, 12.011, 10.996)
    path.AddCurveToPoint(12.007, 10.996, 12.004, 10.996, 12.0, 10.996)
    path.AddLineToPoint(10.0, 10.996)
    path.AddCurveToPoint(9.996, 10.996, 9.993, 10.996, 9.989, 10.996)
    path.AddCurveToPoint(9.446, 10.996, 9.0, 10.55, 9.0, 10.007)
    path.AddCurveToPoint(9.0, 10.003, 9.0, 10.0, 9.0, 9.996)
    path.AddLineToPoint(9.0, 8.0)
    path.CloseSubpath()
    btns.append(Button(path, _alignVCenter, tr("Push selection to vert. center")))
    path = CreatePath()
    path.MoveToPoint(12.0, 12.013)
    path.AddLineToPoint(10.0, 12.013)
    path.AddCurveToPoint(9.441, 12.0, 8.991, 11.532, 9.0, 10.973)
    path.AddLineToPoint(9.0, 6.055)
    path.AddCurveToPoint(8.991, 5.496, 9.441, 5.028, 10.0, 5.015)
    path.AddLineToPoint(12.0, 5.015)
    path.AddCurveToPoint(12.559, 5.028, 13.009, 5.496, 13.0, 6.055)
    path.AddLineToPoint(13.0, 10.973)
    path.CloseSubpath()
    path.MoveToPoint(6.0, 12.013)
    path.AddLineToPoint(4.0, 12.013)
    path.AddCurveToPoint(3.441, 12.0, 2.991, 11.532, 3.0, 10.973)
    path.AddLineToPoint(3.0, 2.04)
    path.AddCurveToPoint(2.991, 1.481, 3.441, 1.013, 4.0, 1.0)
    path.AddLineToPoint(6.0, 1.0)
    path.AddCurveToPoint(6.559, 1.013, 7.009, 1.481, 7.0, 2.04)
    path.AddLineToPoint(7.0, 10.973)
    path.CloseSubpath()
    path.MoveToPoint(16.0, 14.5)
    path.AddCurveToPoint(16.0, 14.224, 15.776, 14.0, 15.5, 14.0)
    path.AddLineToPoint(0.5, 14.0)
    path.AddCurveToPoint(0.224, 14.0, 0.0, 14.224, 0.0, 14.5)
    path.AddCurveToPoint(0.0, 14.776, 0.224, 15.0, 0.5, 15.0)
    path.AddLineToPoint(15.5, 15.0)
    path.CloseSubpath()
    btns.append(Button(path, _alignVBottom, tr("Push selection to bottom")))
    alignmentBar.buttons = btns
    sizer.Add(alignmentBar, 0, wx.EXPAND)
    sizer.AddSpacer(1)
    TransformHeader._tooltips = [
        tr("Scale down"),
        tr("Scale up"),
        tr("Link x/y scale"),
        tr("Rotate counter-clockwise"),
        tr("Rotate clockwise"),
        tr("Skew left"),
        tr("Skew right"),
        tr("Remove overlap"),
        tr("Subtract (selected or top path)"),
        tr("Intersect (selected or top path)"),
        tr("Xor (selected or top path)"),
        tr("Mirror horizontally"),
        tr("Mirror vertically"),
    ]
    sizer.Add(TransformHeader(parent, font), 0, wx.EXPAND)
    sizer.AddSpacer(1)
    sizer.Add(LayersHeader(parent, font), 1, wx.EXPAND)
    # sizer.Add(PadControl(parent), 1, wx.EXPAND)
    return sizer


class Button:
    __slots__ = ("icon", "callback", "tooltip")  # TODO: shortcut

    def __init__(self, icon, callback, tooltip=None):
        self.icon = icon
        self.callback = callback
        self.tooltip = tooltip


class ButtonBar(wx.Window):
    """
    Buttons are tuples of (icon, callback, desc, shortcut).
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.SetBackgroundColor(wx.Colour(240, 240, 240))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._buttons = []
        self._underMouseBtn = None
        self._mouseDownBtn = None

        self._logger = parent._logger


    @property
    def buttons(self):
        return self._buttons

    @buttons.setter
    def buttons(self, btns):
        self._buttons = list(btns)
        self.InvalidateBestSize()
        self.Refresh()

    @property
    def layer(self):
        return wx.GetTopLevelParent(self).activeLayer

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        cnt = len(self._buttons)
        pad = cnt - 1 if cnt else 0
        return wx.Size(8 + cnt * 28 + pad * 4, 36)

    def DoGetIndexForPos(self, pos):
        _, height = self.GetSize()
        if not (4 <= pos.y <= height - 5):
            return
        one = 4 + 28
        base = 4
        for i in range(len(self._buttons)):
            if base + 4 <= pos.x <= base + one:
                return i
            base += one
        return None

    def DoSetToolTip(self, index):
        if index is not None:
            if self._mouseDownBtn is not None:
                return
            btn = self._buttons[index]
            text = btn.tooltip
            # if btn.shortcut:
            #    text += f" ({btn.shortcut})"
        else:
            text = None
        self.SetToolTip(text)

    def OnLeftDown(self, event):
        self._mouseDownBtn = self._underMouseBtn
        self.DoSetToolTip(None)
        self.CaptureMouse()
        self.Refresh()
        # event.Skip()

    def OnMotion(self, event):
        index = self.DoGetIndexForPos(event.GetPosition())
        if self._underMouseBtn != index:
            self.DoSetToolTip(index)
            self._underMouseBtn = index
            self.Refresh()

    def OnLeftUp(self, event):
        self.ReleaseMouse()
        index = self._mouseDownBtn
        if index is None:
            return
        self._mouseDownBtn = None
        if self._underMouseBtn != index:
            return
        self.Refresh()
        layer = self.layer
        if layer:
            glyph = self.layer._parent
            self._logger.info("ALIGN: class {} {} -> operation {}".format(glyph.__class__.__name__ ,glyph.name, self._buttons[index].tooltip))
            self._buttons[index].callback(layer, glyph, self._buttons[index].tooltip)

            trufont.TruFont.updateUI()

    def OnPaint(self, event):
        ctx = wx.GraphicsContext.Create(self)

        ctx.SetBrush(wx.Brush(self.GetBackgroundColour()))
        ctx.DrawRectangle(0, 0, *self.GetSize())

        ctx.Translate(14, 10)
        pressedBrush = wx.Brush(wx.Colour(63, 63, 63))
        brush = wx.Brush(wx.Colour(102, 102, 102))

        for i, btn in enumerate(self._buttons):
            if i == self._mouseDownBtn == self._underMouseBtn:
                b = pressedBrush
            else:
                b = brush
            ctx.SetBrush(b)
            ctx.FillPath(btn.icon)
            ctx.Translate(32, 0)


def SidebarSpinCtrl(*args, **kwargs):
    ctrl = SpinCtrl(*args, **kwargs)
    ctrl.SetForegroundColour(wx.Colour(63, 63, 63))
    # TODO: height is system dependent, though we want to
    # lower it at least on Windows (24->20), GNU (29->25)
    # -- now I get 23 instead of 24 on Windows. wtf?
    h = ctrl.GetSize()[1] - 4
    if h < 20:
        h = 20
    ctrl.SetSize(wx.Size(48, h))
    return ctrl


def _DrawText_Spacing(ctx, text, x, y, sp=1.2):
    offset = 0
    for ch in text:
        ctx.DrawText(ch, x + offset, y)
        offset += ctx.GetTextExtent(ch)[0] + sp


#-------------------------
# Used by undoredo decorator
#-------------------------
def header_expand_params(obj, *args, **kwargs):
    """ use by decorator to get three params as
    layer, undoredomgr and operation """
    return obj.layer, obj._tooltips[obj._underMouseBtn]

header_params_undoredo = {
                         'default':{'copy': (func_copy.copypathsfromlayer, 'layer'),
                                    'undo': (func_copy.undoredo_copypathsfromlayer, 'layer', 'old_paths', 'operation'), 
                                    'redo': (func_copy.undoredo_copypathsfromlayer, 'layer', 'new_paths', 'operation')
                                    },
                         # 'transform':{'copy': (func_copy.copypathsfromlayer, 'layer'),
                         #              'undo': (func_copy.undoredo_fromcopy, 'layer', 'old_datas', 'operation'), 
                         #              'redo': (func_copy.undoredo_fromcopy, 'layer', 'new_datas', 'operation')
                         #             },
                         # 'removeOverlap':{'copy': (func_copy.copypathsfromlayer, 'layer'),
                         #                 'undo': (func_copy.undoredo_fromcopy, 'layer', 'old_datas', 'operation'), 
                         #                 'redo': (func_copy.undoredo_fromcopy, 'layer', 'new_datas', 'operation')
                         #                 },
                         # 'binaryPathOp':{'copy': (func_copy.copypathsfromlayer, 'layer'),
                         #                 'undo': (func_copy.undoredo_fromcopy, 'layer', 'old_datas', 'operation'), 
                         #                 'redo': (func_copy.undoredo_fromcopy, 'layer', 'new_datas', 'operation')
                         #                 },
                        }
#-------------------------

# @deco4class.decorator_classfunc()
class TransformHeader(wx.Panel):
    def __init__(self, parent, font):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        ctrl = self._alignmentCtrl = AlignmentControl(self)
        ctrl.SetPosition(wx.Point(89, 36))
        ctrl.SetSize(ctrl.GetBestSize())

        ctrl = self._scaleCtrl = SidebarSpinCtrl(self)
        ctrl.number = 2
        ctrl.suffix = "%"
        yOffset = ctrl.GetSize()[1] // 2
        ctrl.SetPosition(wx.Point(78, 85 - yOffset))

        ctrl = self._yScaleCtrl = SidebarSpinCtrl(self)
        ctrl.number = 2
        ctrl.suffix = "%"
        ctrl.SetPosition(wx.Point(78, 113 - yOffset))
        ctrl.Enabled = False

        ctrl = self._rotationCtrl = SidebarSpinCtrl(self)
        ctrl.number = 40
        ctrl.suffix = "°"
        ctrl.SetPosition(wx.Point(78, 141 - yOffset))

        ctrl = self._skewCtrl = SidebarSpinCtrl(self)
        ctrl.number = 6
        ctrl.suffix = "°"
        ctrl.SetPosition(wx.Point(78, 169 - yOffset))

        self._mouseDownBtn = None
        self._underMouseBtn = None

        self._logger = parent._logger

    @property
    def layer(self):
        return wx.GetTopLevelParent(self).activeLayer

    @undoredomgr.layer_decorate_undoredo(header_expand_params, 
                                         paths=True, guidelines=False, components=False, anchors=False)
    def binaryPathOp(self, func):
        layer = self.layer
        paths = layer._paths
        if len(paths) < 2:
            return
        target, open_ = None, []
        delIndex = None
        others = list(paths)
        for index, path in enumerate(paths):
            if path.open:
                open_.append(path)
            elif target is None and any(pt.selected for pt in path._points):
                target = path
                delIndex = index
        if delIndex is not None:
            del others[index]
        else:
            target = others.pop(-1)
        paths.clear()
        pen = PathPen(layer.paths)
        func(others, [target], pen)
        paths.extend(open_)
        trufont.TruFont.updateUI()

    @undoredomgr.layer_decorate_undoredo(header_expand_params, 
                                         paths=True, guidelines=False, components=False, anchors=False)
    def removeOverlap(self):
        layer = self.layer
        paths = layer._paths
        target, others = [], []
        useSelection = any(e.__class__ is Point for e in layer.selection)
        for path in paths:
            if path.open:
                others.append(path)
            elif useSelection and not any(pt.selected for pt in path._points):
                others.append(path)
            else:
                target.append(path)
        paths.clear()
        pen = PathPen(layer.paths)
        pathops.union(target, pen)
        paths.extend(others)
        trufont.TruFont.updateUI()

    @undoredomgr.layer_decorate_undoredo(header_expand_params, 
                                         paths=True, guidelines=False, components=False, anchors=False)
    def transform(self, **kwargs):
        layer = self.layer
        transformation = Transformation(**kwargs)
        layer.transform(transformation, selectionOnly=bool(layer.selection))
        trufont.TruFont.updateUI()

    # ----------
    # wx methods
    # ----------

    def DoGetIndexForPos(self, pos):
        rect = wx.Rect(42, 73, 24, 24)
        if rect.Contains(pos):
            return 0
        rect.Offset(96, 0)
        if rect.Contains(pos):
            return 1
        rect.Offset(-96, 28)
        if rect.Contains(pos):
            return 2
        rect.Offset(0, 28)
        if rect.Contains(pos):
            return 3
        rect.Offset(96, 0)
        if rect.Contains(pos):
            return 4
        rect.Offset(-96, 28)
        if rect.Contains(pos):
            return 5
        rect.Offset(96, 0)
        if rect.Contains(pos):
            return 6
        rect.SetTopLeft(wx.Point(8, 185))
        rect.SetWidth(28)
        rect.SetHeight(28)
        if rect.Contains(pos):
            return 7
        rect.Offset(32, 0)
        if rect.Contains(pos):
            return 8
        rect.Offset(32, 0)
        if rect.Contains(pos):
            return 9
        rect.Offset(32, 0)
        if rect.Contains(pos):
            return 10
        rect.Offset(32, 0)
        if rect.Contains(pos):
            return 11
        rect.Offset(32, 0)
        if rect.Contains(pos):
            return 12

    def DoGetBestSize(self):
        return wx.Size(204, 219)

    def DoSetToolTip(self, index):
        if index is not None:
            if self._mouseDownBtn is not None:
                return
            text = self._tooltips[index]
            # +shortcuts?
        else:
            text = None
        self.SetToolTip(text)

    def OnLeftDown(self, event):
        self._mouseDownBtn = self._underMouseBtn
        self.DoSetToolTip(None)
        self.CaptureMouse()
        self.Refresh()
        # event.Skip()

    def OnMotion(self, event):
        index = self.DoGetIndexForPos(event.GetPosition())
        if self._underMouseBtn != index:
            self.DoSetToolTip(index)
            self._underMouseBtn = index
            self.Refresh()

    def OnLeftUp(self, event):
        self.ReleaseMouse()
        index = self._mouseDownBtn
        if index is None:
            return
        self._mouseDownBtn = None
        if self._underMouseBtn != index:
            return
        self.Refresh()
        if self.layer is None:
            pass
        elif index == 0:
            xScale = 1 / (1 + .01 * self._scaleCtrl.number)
            if self._yScaleCtrl.Enabled:
                yScale = 1 / (1 + .01 * self._yScaleCtrl.number)
            else:
                yScale = xScale
            px, py = self._alignmentCtrl.origin
            self.transform(
                xScale=xScale,
                yScale=yScale,
                xOffset=px * (1 - xScale),
                yOffset=py * (1 - yScale),
            )
        elif index == 1:
            xScale = 1 + .01 * self._scaleCtrl.number
            if self._yScaleCtrl.Enabled:
                yScale = 1 + .01 * self._yScaleCtrl.number
            else:
                yScale = xScale
            px, py = self._alignmentCtrl.origin
            self.transform(
                xScale=xScale,
                yScale=yScale,
                xOffset=px * (1 - xScale),
                yOffset=py * (1 - yScale),
            )

        elif index == 2:
            self._yScaleCtrl.Enabled = not self._yScaleCtrl.Enabled
            self.Refresh()

        elif index == 3:
            ca, sa = cos_sin_deg(self._rotationCtrl.number)
            px, py = self._alignmentCtrl.origin
            self.transform(
                xScale=ca,
                xyScale=sa,
                yxScale=-sa,
                yScale=ca,
                xOffset=px - px * ca + py * sa,
                yOffset=py - px * sa - py * ca,
            )
        elif index == 4:
            ca, sa = cos_sin_deg(-self._rotationCtrl.number)
            px, py = self._alignmentCtrl.origin
            self.transform(
                xScale=ca,
                xyScale=sa,
                yxScale=-sa,
                yScale=ca,
                xOffset=px - px * ca + py * sa,
                yOffset=py - px * sa - py * ca,
            )
        elif index == 5:
            angle = math.radians(-self._skewCtrl.number)
            px, py = self._alignmentCtrl.origin
            self.transform(yxScale=angle, xOffset=-py * angle)
        elif index == 6:
            angle = math.radians(self._skewCtrl.number)
            px, py = self._alignmentCtrl.origin
            self.transform(yxScale=angle, xOffset=-py * angle)

        elif index == 7:
            self.removeOverlap()

        elif index == 8:
            self.binaryPathOp(pathops.difference)
        elif index == 9:
            self.binaryPathOp(pathops.intersection)
        elif index == 10:
            self.binaryPathOp(pathops.xor)

        elif index == 11:
            px, _ = self._alignmentCtrl.origin
            self.transform(xScale=-1, xOffset=2 * px)
        elif index == 12:
            _, py = self._alignmentCtrl.origin
            self.transform(yScale=-1, yOffset=2 * py)

    def OnPaint(self, event):
        ctx = wx.GraphicsContext.Create(self)
        font = self.GetFont()
        font.SetPixelSize(wx.Size(0, 10 * platformSpecific.typeSizeScale()))
        ctx.SetFont(font, wx.Colour(120, 120, 120))
        yOffset = 6 - ctx.GetTextExtent("x")[1] // 2

        ctx.SetBrush(wx.Brush(self.GetBackgroundColour()))
        ctx.DrawRectangle(0, 0, *self.GetSize())

        if self._underMouseBtn == self._mouseDownBtn:
            pressedIndex = self._underMouseBtn
        else:
            pressedIndex = None

        _DrawText_Spacing(ctx, "TRANSFORM", 12, 12 + yOffset)

        pressedBrush = wx.Brush(wx.Colour(192, 192, 192))
        pressedPen = wx.Pen(wx.Colour(23, 23, 23))
        brush = wx.Brush(wx.Colour(209, 209, 209))
        pen = wx.Pen(wx.Colour(63, 63, 63))

        ctx.Translate(46, 77)
        path = ctx.CreatePath()
        path.MoveToPoint(9.579, 0.0)
        path.AddCurveToPoint(12.553, 0.0, 15.0, 2.447, 15.0, 5.421)
        path.AddCurveToPoint(15.0, 8.395, 12.553, 10.842, 9.579, 10.842)
        path.AddCurveToPoint(6.605, 10.842, 4.158, 8.395, 4.158, 5.421)
        path.AddCurveToPoint(4.158, 2.447, 6.605, 0.0, 9.579, 0.0)
        path.CloseSubpath()
        ctx.SetBrush(pressedBrush if pressedIndex == 0 else brush)
        ctx.SetPen(pressedPen if pressedIndex == 0 else pen)
        ctx.StrokePath(path)
        ctx.DrawEllipse(0.5, 5.82, 8.68, 8.68)

        ctx.Translate(96, 0)
        ctx.SetBrush(wx.NullBrush)
        ctx.SetPen(pressedPen if pressedIndex == 1 else pen)
        ctx.DrawEllipse(0.5, 5.82, 8.68, 8.68)
        ctx.SetBrush(pressedBrush if pressedIndex == 1 else brush)
        ctx.DrawPath(path)

        pressedBrush_ = wx.Brush(wx.Colour(28, 28, 28))
        brush_ = wx.Brush(wx.Colour(72, 72, 72))

        path = ctx.CreatePath()
        if self._yScaleCtrl.Enabled:
            path.MoveToPoint(2.4, 8.01)
            path.AddCurveToPoint(2.4, 9.67, 3.74, 11.01, 5.4, 11.01)
            path.AddCurveToPoint(6.32, 11.01, 6.67, 10.59, 6.81, 9.93)
            path.AddLineToPoint(5.19, 9.93)
            path.AddCurveToPoint(5.19, 9.93, 3.51, 9.92, 3.51, 8)
            path.AddCurveToPoint(3.51, 6.08, 5.19, 6.07, 5.19, 6.07)
            path.AddLineToPoint(6.81, 6.07)
            path.AddCurveToPoint(6.81, 6.07, 6.31, 5.01, 5.4, 5.01)
            path.AddCurveToPoint(3.74, 5.01, 2.4, 6.36, 2.4, 8.01)
            path.CloseSubpath()
            path.MoveToPoint(12.51, 8)
            path.AddCurveToPoint(12.51, 9.91, 10.52, 9.93, 10.52, 9.93)
            path.AddLineToPoint(9.23, 9.93)
            path.AddCurveToPoint(9.37, 10.59, 9.72, 11.01, 10.64, 11.01)
            path.AddCurveToPoint(12.3, 11.01, 13.64, 9.67, 13.64, 8.01)
            path.AddCurveToPoint(13.64, 6.36, 12.3, 5.01, 10.64, 5.01)
            path.AddCurveToPoint(9.73, 5.01, 9.38, 5.43, 9.24, 6.07)
            path.AddLineToPoint(10.52, 6.07)
            path.AddCurveToPoint(10.52, 6.07, 12.51, 6.09, 12.51, 8)
            path.CloseSubpath()
            path.MoveToPoint(6.38, 2.93)
            path.AddCurveToPoint(6.04, 3.12, 6.44, 3.76, 6.44, 3.76)
            path.AddLineToPoint(6.81, 4.41)
            path.AddCurveToPoint(6.81, 4.41, 7.2, 5.02, 7.5, 4.87)
            path.AddCurveToPoint(7.8, 4.73, 7.44, 4.04, 7.44, 4.04)
            path.AddLineToPoint(7.07, 3.39)
            path.AddCurveToPoint(7.07, 3.39, 6.71, 2.73, 6.38, 2.93)
            path.CloseSubpath()
            path.MoveToPoint(8.5, 4.78)
            path.AddCurveToPoint(8.81, 4.93, 9.21, 4.3, 9.21, 4.3)
            path.AddLineToPoint(9.6, 3.64)
            path.AddCurveToPoint(9.6, 3.64, 10.01, 2.98, 9.67, 2.79)
            path.AddCurveToPoint(9.32, 2.59, 8.95, 3.26, 8.95, 3.26)
            path.AddLineToPoint(8.56, 3.93)
            path.AddCurveToPoint(8.56, 3.93, 8.18, 4.63, 8.5, 4.78)
            path.CloseSubpath()
            path.MoveToPoint(6.32, 13.24)
            path.AddCurveToPoint(6.64, 13.39, 7.04, 12.76, 7.04, 12.76)
            path.AddLineToPoint(7.43, 12.09)
            path.AddCurveToPoint(7.43, 12.09, 7.84, 11.44, 7.49, 11.24)
            path.AddCurveToPoint(7.15, 11.04, 6.78, 11.72, 6.78, 11.72)
            path.AddLineToPoint(6.39, 12.38)
            path.AddCurveToPoint(6.39, 12.38, 6.01, 13.08, 6.32, 13.24)
            path.CloseSubpath()
            path.MoveToPoint(8.53, 11.17)
            path.AddCurveToPoint(8.2, 11.36, 8.59, 12, 8.59, 12)
            path.AddLineToPoint(8.97, 12.65)
            path.AddCurveToPoint(8.97, 12.65, 9.35, 13.27, 9.66, 13.12)
            path.AddCurveToPoint(9.96, 12.97, 9.6, 12.29, 9.6, 12.29)
            path.AddLineToPoint(9.22, 11.64)
            path.AddCurveToPoint(9.22, 11.64, 8.86, 10.98, 8.53, 11.17)
            path.CloseSubpath()
        else:
            path.MoveToPoint(10.646, 11.001)
            path.AddCurveToPoint(9.726, 11.001, 8.915, 10.578, 8.367, 9.923)
            path.AddLineToPoint(10.522, 9.923)
            path.AddCurveToPoint(10.522, 9.923, 12.516, 9.9, 12.516, 7.989)
            path.AddCurveToPoint(12.516, 6.077, 10.522, 6.054, 10.522, 6.054)
            path.AddLineToPoint(8.389, 6.054)
            path.AddCurveToPoint(8.936, 5.414, 9.738, 5.001, 10.646, 5.001)
            path.AddCurveToPoint(12.303, 5.001, 13.645, 6.345, 13.645, 8.001)
            path.AddCurveToPoint(13.645, 9.658, 12.303, 11.001, 10.646, 11.001)
            path.CloseSubpath()
            path.MoveToPoint(4.645, 8.001)
            path.AddCurveToPoint(4.67, 7.306, 5.395, 7.251, 5.395, 7.251)
            path.AddLineToPoint(10.645, 7.251)
            path.AddCurveToPoint(10.645, 7.251, 11.395, 7.209, 11.395, 8.001)
            path.AddCurveToPoint(11.395, 8.793, 10.645, 8.751, 10.645, 8.751)
            path.AddLineToPoint(5.395, 8.751)
            path.AddCurveToPoint(5.395, 8.751, 4.621, 8.697, 4.645, 8.001)
            path.CloseSubpath()
            path.MoveToPoint(3.51, 7.989)
            path.AddCurveToPoint(3.51, 9.909, 5.192, 9.923, 5.192, 9.923)
            path.AddLineToPoint(7.68, 9.923)
            path.AddCurveToPoint(7.132, 10.578, 6.321, 11.001, 5.4, 11.001)
            path.AddCurveToPoint(3.744, 11.001, 2.4, 9.658, 2.4, 8.001)
            path.AddCurveToPoint(2.4, 6.345, 3.744, 5.001, 5.4, 5.001)
            path.AddCurveToPoint(6.309, 5.001, 7.11, 5.414, 7.658, 6.054)
            path.AddLineToPoint(5.192, 6.054)
            path.AddCurveToPoint(5.192, 6.054, 3.51, 6.067, 3.51, 7.989)
            path.CloseSubpath()
        ctx.Translate(-96, 28)
        ctx.SetBrush(pressedBrush_ if pressedIndex == 2 else brush_)
        ctx.SetPen(wx.NullPen)
        ctx.DrawPath(path)

        path = ctx.CreatePath()
        path.MoveToPoint(8.969, 7.989)
        path.AddCurveToPoint(8.969, 7.483, 8.557, 7.071, 8.051, 7.071)
        path.AddCurveToPoint(7.544, 7.071, 7.132, 7.483, 7.132, 7.989)
        path.AddCurveToPoint(7.132, 8.495, 7.544, 8.907, 8.051, 8.907)
        path.AddCurveToPoint(8.557, 8.907, 8.969, 8.495, 8.969, 7.989)
        path.AddCurveToPoint(1.641, 6.074, 1.926, 6.27, 2.221, 6.221)
        path.AddLineToPoint(4.872, 5.74)
        path.AddCurveToPoint(5.168, 5.691, 5.522, 5.514, 5.466, 5.233)
        path.AddCurveToPoint(5.419, 4.952, 4.971, 4.601, 4.686, 4.66)
        path.AddLineToPoint(3.37, 4.896)
        path.AddCurveToPoint(4.195, 3.579, 5.531, 2.607, 7.152, 2.322)
        path.AddCurveToPoint(7.486, 2.264, 7.81, 2.234, 8.144, 2.234)
        path.AddCurveToPoint(10.884, 2.234, 13.232, 4.237, 13.703, 7.007)
        path.AddCurveToPoint(13.969, 8.519, 13.635, 10.051, 12.771, 11.317)
        path.AddCurveToPoint(11.906, 12.584, 10.609, 13.419, 9.116, 13.694)
        path.AddCurveToPoint(8.792, 13.752, 8.458, 13.782, 8.124, 13.782)
        path.AddCurveToPoint(5.383, 13.782, 3.046, 11.769, 2.564, 9.01)
        path.AddLineToPoint(2.506, 8.833)
        path.AddCurveToPoint(2.437, 8.519, 2.25, 8.283, 1.955, 8.283)
        path.AddCurveToPoint(1.671, 8.283, 1.425, 8.548, 1.474, 8.833)
        path.AddLineToPoint(1.504, 9.196)
        path.AddCurveToPoint(2.083, 12.535, 4.922, 14.882, 8.124, 14.882)
        path.AddCurveToPoint(8.517, 14.882, 8.91, 14.842, 9.303, 14.774)
        path.AddCurveToPoint(12.967, 14.116, 15.413, 10.552, 14.764, 6.81)
        path.AddCurveToPoint(14.194, 3.481, 11.346, 1.134, 8.144, 1.134)
        path.AddCurveToPoint(7.761, 1.134, 7.358, 1.164, 6.965, 1.242)
        path.AddCurveToPoint(5.02, 1.586, 3.419, 2.754, 2.437, 4.336)
        path.AddLineToPoint(2.191, 2.872)
        path.AddCurveToPoint(2.133, 2.578, 1.857, 2.372, 1.563, 2.431)
        path.AddCurveToPoint(1.268, 2.479, 1.071, 2.764, 1.13, 3.069)
        path.AddLineToPoint(1.592, 5.769)
        path.AddLineToPoint(1.592, 5.769)
        path.CloseSubpath()
        ctx.Translate(0, 28)
        ctx.SetBrush(pressedBrush_ if pressedIndex == 3 else brush_)
        ctx.DrawPath(path)

        path = ctx.CreatePath()
        path.MoveToPoint(7.031, 7.987)
        path.AddCurveToPoint(7.031, 7.481, 7.443, 7.068, 7.949, 7.068)
        path.AddCurveToPoint(8.456, 7.068, 8.868, 7.481, 8.868, 7.987)
        path.AddCurveToPoint(8.868, 8.493, 8.456, 8.905, 7.949, 8.905)
        path.AddCurveToPoint(7.443, 8.905, 7.031, 8.493, 7.031, 7.987)
        path.CloseSubpath()
        path.MoveToPoint(14.408, 5.767)
        path.AddCurveToPoint(14.359, 6.071, 14.074, 6.268, 13.779, 6.219)
        path.AddLineToPoint(11.127, 5.738)
        path.AddCurveToPoint(10.832, 5.688, 10.477, 5.512, 10.534, 5.231)
        path.AddCurveToPoint(10.581, 4.949, 11.029, 4.598, 11.314, 4.658)
        path.AddLineToPoint(12.63, 4.893)
        path.AddCurveToPoint(11.805, 3.577, 10.469, 2.605, 8.848, 2.32)
        path.AddCurveToPoint(8.514, 2.261, 8.19, 2.232, 7.856, 2.232)
        path.AddCurveToPoint(5.116, 2.232, 2.768, 4.235, 2.297, 7.004)
        path.AddCurveToPoint(2.031, 8.516, 2.365, 10.048, 3.229, 11.315)
        path.AddCurveToPoint(4.094, 12.582, 5.391, 13.416, 6.884, 13.691)
        path.AddCurveToPoint(7.208, 13.75, 7.542, 13.78, 7.876, 13.78)
        path.AddCurveToPoint(10.617, 13.78, 12.954, 11.767, 13.436, 9.008)
        path.AddLineToPoint(13.494, 8.831)
        path.AddCurveToPoint(13.563, 8.516, 13.75, 8.281, 14.045, 8.281)
        path.AddCurveToPoint(14.329, 8.281, 14.575, 8.546, 14.526, 8.831)
        path.AddLineToPoint(14.496, 9.194)
        path.AddCurveToPoint(13.917, 12.533, 11.078, 14.879, 7.876, 14.879)
        path.AddCurveToPoint(7.483, 14.879, 7.09, 14.84, 6.697, 14.772)
        path.AddCurveToPoint(3.033, 14.114, 0.587, 10.549, 1.236, 6.808)
        path.AddCurveToPoint(1.806, 3.479, 4.654, 1.132, 7.856, 1.132)
        path.AddCurveToPoint(8.239, 1.132, 8.642, 1.161, 9.035, 1.24)
        path.AddCurveToPoint(10.98, 1.584, 12.581, 2.752, 13.563, 4.333)
        path.AddLineToPoint(13.809, 2.87)
        path.AddCurveToPoint(13.867, 2.576, 14.143, 2.369, 14.437, 2.428)
        path.AddCurveToPoint(14.732, 2.477, 14.929, 2.762, 14.87, 3.066)
        path.CloseSubpath()
        ctx.Translate(96, 0)
        ctx.SetBrush(pressedBrush_ if pressedIndex == 4 else brush_)
        ctx.DrawPath(path)

        path = ctx.CreatePath()
        path.MoveToPoint(1.3, 1.0)
        path.AddLineToPoint(6.5, 1.0)
        path.AddCurveToPoint(6.78, 1.0, 6.8, 1.1, 7.0, 1.5)
        path.AddLineToPoint(13.0, 13.5)
        path.AddCurveToPoint(13.16, 13.78, 13.05, 14.0, 12.7, 14.0)
        path.AddLineToPoint(7.5, 14.0)
        path.AddCurveToPoint(7.22, 14.0, 7.2, 13.9, 7.0, 13.5)
        path.AddLineToPoint(1.0, 1.5)
        path.AddCurveToPoint(0.85, 1.22, 0.95, 1.0, 1.3, 1.0)
        path_ = ctx.CreatePath()
        path_.MoveToPoint(10, 1)
        path_.AddLineToPoint(14, 1)
        path_.AddLineToPoint(14, 9)
        ctx.Translate(-96, 28)
        ctx.SetBrush(pressedBrush if pressedIndex == 5 else brush)
        ctx.SetPen(pressedPen if pressedIndex == 5 else pen)
        ctx.DrawPath(path)
        ctx.StrokePath(path_)

        path = ctx.CreatePath()
        path.MoveToPoint(13.7, 1.0)
        path.AddLineToPoint(8.5, 1.0)
        path.AddCurveToPoint(8.22, 1.0, 8.2, 1.1, 8.0, 1.5)
        path.AddLineToPoint(2.0, 13.5)
        path.AddCurveToPoint(1.84, 13.78, 1.95, 14.0, 2.3, 14.0)
        path.AddLineToPoint(7.5, 14.0)
        path.AddCurveToPoint(7.78, 14.0, 7.8, 13.9, 8.0, 13.5)
        path.AddLineToPoint(14.0, 1.5)
        path.AddCurveToPoint(14.15, 1.22, 14.05, 1.0, 13.7, 1.0)
        path_ = ctx.CreatePath()
        path_.MoveToPoint(5, 1)
        path_.AddLineToPoint(1, 1)
        path_.AddLineToPoint(1, 9)
        ctx.Translate(96, 0)
        ctx.SetBrush(pressedBrush if pressedIndex == 6 else brush)
        ctx.SetPen(pressedPen if pressedIndex == 6 else pen)
        ctx.DrawPath(path)
        ctx.StrokePath(path_)

        path = ctx.CreatePath()
        path.MoveToPoint(5.5, 14.0)
        path.AddCurveToPoint(5.226, 14.0, 5.0, 13.774, 5.0, 13.5)
        path.AddLineToPoint(5.0, 10.0)
        path.AddLineToPoint(1.5, 10.0)
        path.AddCurveToPoint(1.226, 10.0, 1.0, 9.774, 1.0, 9.5)
        path.AddLineToPoint(1.0, 1.5)
        path.AddCurveToPoint(1.0, 1.226, 1.226, 1.0, 1.5, 1.0)
        path.AddLineToPoint(9.5, 1.0)
        path.AddCurveToPoint(9.774, 1.0, 10.0, 1.226, 10.0, 1.5)
        path.AddLineToPoint(10.0, 5.0)
        path.AddLineToPoint(13.5, 5.0)
        path.AddCurveToPoint(13.774, 5.0, 14.0, 5.226, 14.0, 5.5)
        path.AddLineToPoint(14.0, 13.5)
        path.AddCurveToPoint(14.0, 13.774, 13.774, 14.0, 13.5, 14.0)
        path.CloseSubpath()
        ctx.Translate(-128, 30)
        ctx.SetBrush(pressedBrush if pressedIndex == 7 else brush)
        ctx.SetPen(pressedPen if pressedIndex == 7 else pen)
        ctx.DrawPath(path)

        path = ctx.CreatePath()
        path.MoveToPoint(5.0, 10.0)
        path.AddLineToPoint(1.5, 10.0)
        path.AddCurveToPoint(1.226, 10.0, 1.0, 9.774, 1.0, 9.5)
        path.AddLineToPoint(1.0, 1.5)
        path.AddCurveToPoint(1.0, 1.226, 1.226, 1.0, 1.5, 1.0)
        path.AddLineToPoint(9.5, 1.0)
        path.AddCurveToPoint(9.774, 1.0, 10.0, 1.226, 10.0, 1.5)
        path.AddLineToPoint(10.0, 5.0)
        path.AddLineToPoint(5.5, 5.0)
        path.AddCurveToPoint(5.226, 5.0, 5.0, 5.226, 5.0, 5.5)
        path.CloseSubpath()
        path_ = ctx.CreatePath()
        path_.MoveToPoint(14.0, 5.5)
        path_.AddCurveToPoint(14.0, 5.224, 13.776, 5.0, 13.5, 5.0)
        path_.AddLineToPoint(5.5, 5.0)
        path_.AddCurveToPoint(5.224, 5.0, 5.0, 5.224, 5.0, 5.5)
        path_.AddLineToPoint(5.0, 13.5)
        path_.AddCurveToPoint(5.0, 13.776, 5.224, 14.0, 5.5, 14.0)
        path_.AddLineToPoint(13.5, 14.0)
        path_.AddCurveToPoint(13.776, 14.0, 14.0, 13.776, 14.0, 13.5)
        path_.CloseSubpath()
        ctx.Translate(32, 0)
        ctx.SetBrush(pressedBrush if pressedIndex == 8 else brush)
        ctx.SetPen(pressedPen if pressedIndex == 8 else pen)
        ctx.DrawPath(path)
        ctx.StrokePath(path_)

        path = ctx.CreatePath()
        path.MoveToPoint(10.0, 1.5)
        path.AddCurveToPoint(10.0, 1.224, 9.776, 1.0, 9.5, 1.0)
        path.AddLineToPoint(1.5, 1.0)
        path.AddCurveToPoint(1.224, 1.0, 1.0, 1.224, 1.0, 1.5)
        path.AddLineToPoint(1.0, 9.5)
        path.AddCurveToPoint(1.0, 9.776, 1.224, 10.0, 1.5, 10.0)
        path.AddLineToPoint(9.5, 10.0)
        path.AddCurveToPoint(9.776, 10.0, 10.0, 9.776, 10.0, 9.5)
        path.CloseSubpath()
        path.MoveToPoint(14.0, 5.5)
        path.AddCurveToPoint(14.0, 5.224, 13.776, 5.0, 13.5, 5.0)
        path.AddLineToPoint(5.5, 5.0)
        path.AddCurveToPoint(5.224, 5.0, 5.0, 5.224, 5.0, 5.5)
        path.AddLineToPoint(5.0, 13.5)
        path.AddCurveToPoint(5.0, 13.776, 5.224, 14.0, 5.5, 14.0)
        path.AddLineToPoint(13.5, 14.0)
        path.AddCurveToPoint(13.776, 14.0, 14.0, 13.776, 14.0, 13.5)
        path.CloseSubpath()
        path_ = ctx.CreatePath()
        path_.MoveToPoint(5.0, 10.0)
        path_.AddLineToPoint(5.0, 5.5)
        path_.AddCurveToPoint(5.0, 5.226, 5.226, 5.0, 5.5, 5.0)
        path_.AddLineToPoint(10.0, 5.0)
        path_.AddLineToPoint(10.0, 9.5)
        path_.AddCurveToPoint(10.0, 9.774, 9.774, 10.0, 9.5, 10.0)
        path_.CloseSubpath()
        ctx.Translate(32, 0)
        ctx.SetBrush(pressedBrush if pressedIndex == 9 else brush)
        ctx.SetPen(pressedPen if pressedIndex == 9 else pen)
        ctx.StrokePath(path)
        ctx.DrawPath(path_)

        ctx.Translate(32, 0)

        ctx.SetBrush(pressedBrush if pressedIndex == 10 else brush)
        ctx.SetPen(pressedPen if pressedIndex == 10 else pen)
        ctx.DrawPath(path)
        ctx.StrokePath(path_)

        pressedBrush = wx.Brush(wx.Colour(63, 63, 63))
        brush = wx.Brush(wx.Colour(102, 102, 102))

        path = ctx.CreatePath()
        path.MoveToPoint(11.0, 13.0)
        path.AddCurveToPoint(10.451, 13.0, 10.0, 12.549, 10.0, 12.0)
        path.AddLineToPoint(10.0, 4.0)
        path.AddCurveToPoint(10.0, 3.451, 10.451, 3.0, 11.0, 3.0)
        path.AddLineToPoint(13.0, 3.0)
        path.AddCurveToPoint(13.549, 3.0, 14.0, 3.451, 14.0, 4.0)
        path.AddLineToPoint(14.0, 12.0)
        path.AddCurveToPoint(14.0, 12.549, 13.549, 13.0, 13.0, 13.0)
        path.CloseSubpath()
        path.MoveToPoint(2.0, 13.0)
        path.AddCurveToPoint(1.451, 13.0, 1.0, 12.549, 1.0, 12.0)
        path.AddLineToPoint(1.0, 4.0)
        path.AddCurveToPoint(1.0, 3.451, 1.451, 3.0, 2.0, 3.0)
        path.AddLineToPoint(4.0, 3.0)
        path.AddCurveToPoint(4.549, 3.0, 5.0, 3.451, 5.0, 4.0)
        path.AddLineToPoint(5.0, 12.0)
        path.AddCurveToPoint(5.0, 12.549, 4.549, 13.0, 4.0, 13.0)
        path.CloseSubpath()
        path.MoveToPoint(2.0, 4.0)
        path.AddLineToPoint(2.0, 12.0)
        path.AddLineToPoint(4.0, 12.0)
        path.AddLineToPoint(4.0, 4.0)
        path.CloseSubpath()
        path.MoveToPoint(8.0, 0.5)
        path.AddCurveToPoint(8.0, 0.224, 7.776, 0.0, 7.5, 0.0)
        path.AddCurveToPoint(7.224, 0.0, 7.0, 0.224, 7.0, 0.5)
        path.AddLineToPoint(7.0, 15.5)
        path.AddCurveToPoint(7.0, 15.776, 7.224, 16.0, 7.5, 16.0)
        path.AddCurveToPoint(7.776, 16.0, 8.0, 15.776, 8.0, 15.5)
        path.CloseSubpath()
        ctx.Translate(32, 0)
        ctx.SetBrush(pressedBrush if pressedIndex == 11 else brush)
        ctx.SetPen(wx.NullPen)
        ctx.DrawPath(path)

        path = ctx.CreatePath()
        path.MoveToPoint(4.0, 6.01)
        path.AddCurveToPoint(3.451, 6.01, 3.0, 5.559, 3.0, 5.01)
        path.AddLineToPoint(3.0, 3.0)
        path.AddCurveToPoint(3.0, 2.451, 3.451, 2.0, 4.0, 2.0)
        path.AddLineToPoint(12.0, 2.0)
        path.AddCurveToPoint(12.549, 2.0, 13.0, 2.451, 13.0, 3.0)
        path.AddLineToPoint(13.0, 5.0)
        path.AddCurveToPoint(13.0, 5.003, 13.0, 5.007, 13.0, 5.01)
        path.AddCurveToPoint(13.0, 5.559, 12.549, 6.01, 12.0, 6.01)
        path.CloseSubpath()
        path.MoveToPoint(12.0, 10.99)
        path.AddCurveToPoint(12.549, 10.99, 13.0, 11.441, 13.0, 11.99)
        path.AddLineToPoint(13.0, 13.99)
        path.AddCurveToPoint(13.0, 14.539, 12.549, 14.99, 12.0, 14.99)
        path.AddLineToPoint(4.0, 14.99)
        path.AddCurveToPoint(3.451, 14.99, 3.0, 14.539, 3.0, 13.99)
        path.AddLineToPoint(3.0, 11.99)
        path.AddCurveToPoint(3.0, 11.441, 3.451, 10.99, 4.0, 10.99)
        path.CloseSubpath()
        path.MoveToPoint(12.0, 14.0)
        path.AddLineToPoint(12.0, 12.0)
        path.AddLineToPoint(4.0, 12.0)
        path.AddLineToPoint(4.0, 14.0)
        path.CloseSubpath()
        path.MoveToPoint(15.5, 9.0)
        path.AddCurveToPoint(15.776, 9.0, 16.0, 8.776, 16.0, 8.5)
        path.AddCurveToPoint(16.0, 8.224, 15.776, 8.0, 15.5, 8.0)
        path.AddLineToPoint(0.5, 8.0)
        path.AddCurveToPoint(0.224, 8.0, 0.0, 8.224, 0.0, 8.5)
        path.AddCurveToPoint(0.0, 8.776, 0.224, 9.0, 0.5, 9.0)
        path.CloseSubpath()
        ctx.Translate(32, 0)
        ctx.SetBrush(pressedBrush if pressedIndex == 12 else brush)
        ctx.DrawPath(path)


class LayersHeader(wx.Panel):
    def __init__(self, parent, font):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        # XXX: when resized (wx.EXPAND), layersView should resize
        # accordingly
        self._layersView = LayersView(self, font)
        self._layersView.SetSize(wx.Size(204, 102))
        self._layersView.SetPosition(wx.Point(0, 34))

    def OnActiveLayerChanged(self, event):
        self.Refresh()

    # ----------
    # wx methods
    # ----------

    def DoCreateLayer(self):
        # this logic should probably be in the model
        view = self._layersView
        layer = view._activeLayer
        # XXX we should rather disable the icon!
        if layer is None:
            return
        layers = layer._parent.layers
        layers.append(layer.copy())
        """
        # collect existing colors and set
        colors = set(tuple(ly.color) for ly in layers if ly.color)
        for c in self.colors:
            if c in colors:
                continue
            l.color = c
            break
        """
        trufont.TruFont.updateUI()

    def DoGetBestSize(self):
        return wx.Size(204, 148)

    def OnLeftDown(self, event):
        pos = event.GetPosition()
        width, _ = self.GetSize()
        if wx.Rect(width - 26, 11, 16, 16).Contains(pos):
            self.DoCreateLayer()

    def OnPaint(self, event):
        ctx = wx.GraphicsContext.Create(self)
        font = self.GetFont()
        font.SetPixelSize(wx.Size(0, 10 * platformSpecific.typeSizeScale()))
        ctx.SetFont(font, wx.Colour(120, 120, 120))
        yOffset = 6 - ctx.GetTextExtent("x")[1] // 2
        width, _ = self.GetSize()

        ctx.SetBrush(wx.Brush(self.GetBackgroundColour()))
        ctx.DrawRectangle(0, 0, *self.GetSize())

        _DrawText_Spacing(ctx, "LAYERS", 12, 12 + yOffset)
        ctx.Translate(width - 26, 11)
        ctx.SetBrush(wx.Brush(wx.Colour(102, 102, 102)))
        ctx.DrawPath(path)

    def OnSize(self, event):
        self._layersView.Refresh()


class PadControl(wx.Window):
    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

    def DoGetBestSize(self):
        return wx.Size(0, 0)

    def OnPaint(self, event):
        ctx = wx.GraphicsContext.Create(self)
        width, _ = self.GetSize()

        ctx.SetBrush(wx.Brush(self.GetBackgroundColour()))
        ctx.DrawRectangle(0, 0, *self.GetSize())

        ctx.SetPen(wx.Pen(wx.Colour(204, 204, 204)))
        ctx.StrokeLine(0, 0, width, 0)
