class GuidelineSegment:
    __slots__ = "guideline"

    def __init__(self, guideline):
        self.guideline = guideline


class PointRecord:
    __slots__ = ("point", "index")

    def __init__(self, point, index):
        self.point = point
        self.index = index

    @property
    def path(self):
        return self.point._parent

    @property
    def points(self):
        return self.point._parent._points


class SegmentRecord:
    __slots__ = ("segments", "index")

    def __init__(self, segments, index):
        self.segments = segments
        self.index = index

    @property
    def path(self):
        return self.segments._points._parent

    @property
    def points(self):
        return self.segments._points

    @property
    def segment(self):
        return self.segments[self.index]
