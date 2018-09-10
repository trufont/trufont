from copy import copy
from tfont.objects import Path


def atOpenBoundary(point):
    path = point._parent
    if path.open:
        points = path.points
        return points[0] is point or points[-1] is point
    return False


# Path.breakAt(index) ?
def breakPath(path, index):
    points = path._points
    point = points[index]
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
    otherPoint._parent = None  # we should define __copy__ on Point to not
                               # have to do this
    otherPoint.selected = False
    points.append(otherPoint)
    point.type = "move"
    points.applyChange()


# Layer.joinPaths() ?
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
