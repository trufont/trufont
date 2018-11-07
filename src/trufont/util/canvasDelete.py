from copy import copy
from tfont.objects import Path

# TODO: fold this into canvasOps when ready?
import trufont.util.deco4class as deco4class

import trufont.objects.undoredomgr as undoredomgr
import trufont.util.func_copy as func_copy

#-------------------------
# Used by undoredo decorator
#-------------------------
def deleteUILayer_expand_params(obj, *args, **kwargs):
    """ use by decorator to get three params as  
    layer, undoredomgr and operation """

    return obj, "Delete selection" 

deleteUILayer_params_undoredo = { 
                       'deleteUILayerSelection':{'copy': (func_copy.copylayerfromlayer, 'layer'),
                                                'undo': (func_copy.undoredo_copylayerfromlayer, 'layer', 'old_layer', 'operation'), 
                                                'redo': (func_copy.undoredo_copylayerfromlayer, 'layer', 'new_layer', 'operation')
                                                }
                        }
# @deco4class.func_decorator
@undoredomgr.layer_decorate_undoredo(deleteUILayer_expand_params)
def deleteUILayerSelection(layer, breakPaths=False):
#    layer.beginUndoGroup()
    anchors = layer._anchors
    for name in list(anchors):
        if anchors[name].selected:
            del anchors[name]
    components = layer._components
    for index in reversed(range(len(components))):
        if components[index].selected:
            del components[index]
    guidelines = layer._guidelines
    for index in reversed(range(len(guidelines))):
        if guidelines[index].selected:
            del guidelines[index]
    if breakPaths:
        paths = deleteSelection(layer._paths)
    else:
        paths = foldSelection(layer._paths)
    layer.clearSelection()
    layer._paths = paths
    layer.paths.applyChange()
    """
    if layer.image.selected:
        layer.image = None
    """
 #   undoLambda, redoLambda = layer.endUndoGroup()
    # layer._parent is an instance of class Truglyph
 #   layer._parent.get_undoredo().append_action(undoredomgr.Action("Delete selection", undoLambda, redoLambda))


def deleteSelection(paths):
    paths = filterSelection(paths, invert=True)
    outPaths = []
    for path in paths:
        segments = path.segments
        if not path.open and not segments[0].offSelected:
            firstIndex = 0
            for segment in reversed(segments):
                firstIndex -= 1
                if segment.offSelected:
                    break
            size = len(segments)
            if firstIndex == -size:
                # none selected, bring on the original path
                outPaths.append(path)
                continue
            else:
                firstIndex += size
                iterable = segments.iterfrom(firstIndex)
        else:
            iterable = segments
        outPath = None
        for segment in iterable:
            if segment.offSelected or segment.type == "move":
                if outPath is not None:
                    outPaths.append(outPath)
                outPath = Path()
                outPath._parent = path._parent
                outPoints = outPath.points
                point = segment.onCurve
                point.smooth = False
                point.type = "move"
                outPoints.append(point)
            else:
                outPoints.extend(segment.penPoints)
        outPaths.append(outPath)
    return outPaths


def filterSelection(paths, invert=False):
    selValue = not invert
    outPaths = []
    for path in paths:
        segments = path.segments
        if not path.open and segments[0].onSelected == selValue:
            firstIndex = 0
            for segment in reversed(segments):
                if segment.onSelected == selValue:
                    firstIndex -= 1
                else:
                    break
            size = len(segments)
            if firstIndex == -size:
                # all selected, bring on the original path
                outPaths.append(path)
                continue
            else:
                firstIndex += size
                iterable = segments.iterfrom(firstIndex)
        else:
            iterable = segments
        prevSelected = False
        for segment in iterable:
            selected = segment.onSelected == selValue
            if selected:
                if prevSelected:
                    outPoints.extend(segment.penPoints)
                else:
                    outPath = Path()
                    if invert:
                        outPath._parent = path._parent
                        outPoints = outPath.points
                        point = segment.onCurve
                    else:
                        outPoints = outPath._points
                        point = copy(segment.onCurve)
                        point._parent = None
                    point.smooth = False
                    point.type = "move"
                    outPoints.append(point)
            else:
                if prevSelected:
                    if invert:
                        prev.onCurve.smooth = False
                    # we got a path, export it and move on
                    outPaths.append(outPath)
                    outPath = outPoints = None
            prev = segment
            prevSelected = selected
        if prevSelected:
            outPaths.append(outPath)
        outPath = outPoints = None
    return outPaths


def foldSelection(paths):
    outPaths = []
    for path in paths:
        segments = path.segments
        forwardMove = False
        for idx in reversed(range(len(segments))):
            segment = segments[idx]
            if segment.onSelected:
                if not idx and segment.type == "move":
                    forwardMove = True
                del segments[idx]
            elif segment.offSelected:
                segment.removeOffCurves()
        points = path._points
        if not points:
            continue
        if forwardMove:
            segment = segments[0]
            del points[segment._start : segment._end]
            start = points[0]
            start.smooth = False
            start.type = "move"
        outPaths.append(path)
    return outPaths
