from math import atan2, isclose, pi
from tfont.objects import Path, Point


class PathPen:
    # paths: List[Path]
    # points: List[Points]

    def __init__(self, paths):
        self.paths = paths

    def _smoothJoin(self, p1x, p1y):
        last = self.points[-1]
        lastOff = self.points[-2]
        angle = abs(
            atan2(p1y - last.y, p1x - last.x) -
            atan2(lastOff.y - last.y, lastOff.x - last.x)
        )
        return isclose(angle, pi)

    def closePath(self):
        pt = self.points.pop(0)
        assert pt.type == "move"
        last = self.points[-1]
        if not (isclose(pt.x, last.x) and isclose(pt.y, last.y)):
            pt.type = "line"
            self.points.append(pt)
        elif self.checkSmoothStart and last.type == "curve":
            off = self.points[0]
            last.smooth = self._smoothJoin(off.x, off.y)

    def moveTo(self, pt):
        path = Path()
        self.paths.append(path)
        self.points = path.points
        self.points.append(Point(*pt, "move"))
        self.checkSmoothStart = False

    def lineTo(self, pt):
        self.points.append(Point(*pt, "line"))

    def curveTo(self, pt1, pt2, pt3):
        last = self.points[-1]
        if last.type == "curve":
            last.smooth = self._smoothJoin(*pt1)
        elif last.type == "move":
            self.checkSmoothStart = True
        self.points.append(Point(*pt1))
        self.points.append(Point(*pt2))
        self.points.append(Point(*pt3, "curve"))

    def qCurveTo(self, *pts):
        raise NotImplementedError


def draw(self, pen):
        points = self._points
        if not points:
            return
        start = points[0]
        open_ = skip = start.type == "move"
        if open_:
            pen.moveTo((start.x, start.y))
        else:
            start = points[-1]
            assert start.type is not None
            pen.moveTo((start.x, start.y))
        stack = []
        for point in points:
            if skip:
                skip = False
            elif point.type == "line":
                assert not stack
                pen.lineTo((point.x, point.y))
            else:
                stack.append((point.x, point.y))
                if point.type == "curve":
                    pen.curveTo(*stack)
                    stack = []
        if not open_:
            pen.closePath()
Path.draw = draw
