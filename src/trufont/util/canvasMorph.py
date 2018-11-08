from copy import copy
from tfont.objects import Path

import trufont.objects.undoredomgr as undoredomgr


def atOpenBoundary(point):
    path = point._parent
    if path.open:
        points = path.points
        return points[0] is point or points[-1] is point
    return False


#-------------------------
# Used by undoredo decorator
#-------------------------
def path_expand_params(obj, *args, **kwargs):
    """ return layer of object here a path"""
    return obj._parent
#-------------------------

@undoredomgr.layer_decorate_undoredo(path_expand_params, operation="Break path", 
                                     paths=True, guidelines=False, components=False, anchors=False)
def breakPath(path, index):
    points = path._points
    point = points[index]
    point.smooth = False
    if path.open:
        otherPath = Path()
        otherPoints = otherPath.points
        otherPoints.extend(points[index:])
        points[:] = points[:index]
        path._parent.paths.append(otherPath)
    else:
        points[:] = points[index:] + points[:index]
    points = path.points
    otherPoint = copy(point)
    # we should define __copy__ on Point to not have to do this
    otherPoint._parent = None
    otherPoint.selected = False
    points.append(otherPoint)
    point.type = "move"
    points.applyChange()


# Layer.joinPaths() ?
@undoredomgr.layer_decorate_undoredo(path_expand_params, operation="Join paths", 
                                     paths=True, guidelines=False, components=False, anchors=False)
def joinPaths(path, atStart, otherPath, atOtherStart, mergeJoin=False):
    if path is otherPath:
        if atStart == atOtherStart:
            return
        if atStart:
            path.reverse()
        path.close()
        if mergeJoin:
            del path.points[-1]
            # here lastPoint might not have precisely the same position as the
            # dupl. point we just pruned, use moveUIPoint to put it in position
    else:
        if atStart:
            path.reverse()
        if not atOtherStart:
            otherPath.reverse()
        points = path.points
        if mergeJoin:
            pointType = points.pop().type
        else:
            pointType = "line"
        layer = path._parent
        layer.clearSelection()
        otherPoints = otherPath._points
        points.extend(otherPoints)
        layer.paths.remove(otherPath)
        otherFirstPoint = otherPoints[0]
        otherFirstPoint.type = pointType
        otherFirstPoint.selected = True
