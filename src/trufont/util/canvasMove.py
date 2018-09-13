from trufont.util import bezierMath


def nudgeUICurve(on1, off1, off2, on2, dx, dy):
    if on2.selected != on1.selected:
        sign = -on1.selected or 1
        sdx = sign * dx
        sdy = sign * dy
        # factor
        xFactor = on2.x - on1.x - sdx
        if xFactor:
            xFactor = (on2.x - on1.x) / xFactor
        yFactor = on2.y - on1.y - sdy
        if yFactor:
            yFactor = (on2.y - on1.y) / yFactor
        # apply
        if not off1.selected:
            off1.x = on1.x + xFactor * (off1.x - on1.x)
            off1.y = on1.y + yFactor * (off1.y - on1.y)
        if not off2.selected:
            off2.x = on1.x + xFactor * (off2.x - on1.x - sdx)
            off2.y = on1.y + yFactor * (off2.y - on1.y - sdy)


# remove this, give this signature to lineProjection()
def projectUIPointOnRefLine(x1, y1, x2, y2, pt):
    x, y, _ = bezierMath.lineProjection(x1, y1, x2, y2, pt.x, pt.y, False)
    # TODO: use grid precision ROUND
    pt.x = x  # round(x)
    pt.y = y  # round(y)


def rotateUIPointAroundRefLine(x1, y1, x2, y2, pt):
    """
    Given three points p1, p2, pt this rotates pt around p2 such that p1,p2 and
    p1,pt are collinear.
    """
    # we could probably use squared distance here, at least inline the calculus
    p2p_l = bezierMath.distance(pt.x, pt.y, x2, y2)
    p1p2_l = bezierMath.distance(x1, y1, x2, y2)
    if not p1p2_l:
        return
    t = (p1p2_l + p2p_l) / p1p2_l
    # TODO: use grid precision ROUND
    pt.x = x1 + (x2 - x1) * t
    pt.y = y1 + (y2 - y1) * t


def moveUILayerSelection(layer, dx, dy, option=None):
    # layer.beginUndoGroup()
    for anchor in layer.anchors:
        if anchor.selected:
            anchor.x += dx
            anchor.y += dy
    for component in layer.components:
        if component.selected:
            transformation = component.transformation
            transformation.xOffset += dx
            transformation.yOffset += dy
    master = layer.master
    if master is not None:
        guidelines = layer._guidelines + master._guidelines
    else:
        guidelines = layer._guidelines
    for guideline in guidelines:
        if guideline.selected:
            guideline.x += dx
            guideline.y += dy
    for path in layer.paths:
        moveUIPathSelection(
            path, dx, dy, nudgePoints=option == "nudge", slidePoints=option == "slide"
        )
        path.points.applyChange()
    """
    image = layer.image
    if image.selected:
        image.move(delta)
    """
    # layer.endUndoGroup()


def moveUIPathSelection(path, dx, dy, nudgePoints=False, slidePoints=False):
    points = path._points
    len_points = len(points)
    if len_points < 2:
        try:
            point = points[0]
        except IndexError:
            pass
        else:
            if point.selected:
                point.x += dx
                point.y += dy
        return
    # first pass: move
    didMove = False
    prevOn = None
    prev = points[-2]
    point = points[-1]
    for next_ in points:
        selected = point.selected
        didMove |= selected
        if selected:
            point.x += dx
            point.y += dy
        if not slidePoints:
            if point.type is not None:
                if selected:
                    if prev.type is None and not prev.selected and point.type != "move":
                        prev.x += dx
                        prev.y += dy
                    if next_.type is None and not next_.selected:
                        next_.x += dx
                        next_.y += dy
                prevOn = point
            if nudgePoints and next_.type == "curve":
                # XXX next_ hasn't moved yet
                nudgeUICurve(prevOn, prev, point, next_, dx, dy)
        prev, point = point, next_
    if not didMove or len_points < 3:
        return
    # second pass: constrain
    for next_ in points:
        atNode = point.type is not None and prev.type is None or next_.type is None
        # slide points
        if atNode and slidePoints:
            p1, p2, p3 = prev, point, next_
            if p2.selected and p2.type != "move":
                if p1.selected or p3.selected:
                    if p1.selected:
                        p1, p3 = p3, p1
                    # if p3 is selected, we just let it move freely
                    if not p1.selected and p3.type is None:
                        rotateUIPointAroundRefLine(p1.x, p1.y, p2.x, p2.y, p3)
                else:
                    if p2.smooth:
                        projectUIPointOnRefLine(p1.x, p1.y, p3.x, p3.y, p2)
            elif p1.selected != p3.selected:
                if p1.selected:
                    p1, p3 = p3, p1
                if p3.type is None:
                    if p2.smooth and p2.type != "move":
                        projectUIPointOnRefLine(p1.x, p1.y, p2.x, p2.y, p3)
                    else:
                        rx, ry = p3.x - dx, p3.y - dy
                        projectUIPointOnRefLine(p2.x, p2.y, rx, ry, p3)
        # rotation/projection across smooth onCurve
        if atNode and point.smooth and point.type != "move":
            p1, p2, p3 = prev, point, next_
            if p2.selected:
                if p1.type is None:
                    p1, p3 = p3, p1
                if p1.type is not None:
                    rotateUIPointAroundRefLine(p1.x, p1.y, p2.x, p2.y, p3)
            elif p1.selected != p3.selected:
                if p1.selected:
                    p1, p3 = p3, p1
                if p1.type is not None:
                    projectUIPointOnRefLine(p1.x, p1.y, p2.x, p2.y, p3)
                elif not slidePoints:
                    rotateUIPointAroundRefLine(p3.x, p3.y, p2.x, p2.y, p1)
        # --
        prev, point = point, next_
