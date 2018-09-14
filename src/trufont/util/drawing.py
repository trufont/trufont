from math import atan2, cos, pi, radians, sin
import wx

_rdr = wx.GraphicsRenderer.GetDefaultRenderer()

CreateMatrix = _rdr.CreateMatrix
CreateMeasuringContext = _rdr.CreateMeasuringContext
CreatePath = _rdr.CreatePath

# -----------------
# Convenience funcs
# -----------------


def cos_sin_deg(deg):
    deg = deg % 360.0
    if deg == 90:
        return 0.0, 1.0
    elif deg == 180:
        return -1.0, 0
    elif deg == 270:
        return 0, -1.0
    rad = radians(deg)
    return cos(rad), sin(rad)


def drawTextAtPoint(
    ctx, text, x, y, scale, xAlign="left", yAlign="bottom", flipped=True
):
    # TODO: can we natively draw multiline text?
    _, lineHeight = ctx.GetTextExtent("x")
    lines = text.splitlines()
    if xAlign != "left" or yAlign != "bottom":
        width = scale * max(ctx.GetTextExtent(line)[0] for line in lines)
        height = scale * len(lines) * lineHeight
        dh = -height if flipped else height
        if xAlign == "center":
            x -= width / 2
        elif xAlign == "right":
            x -= width
        if yAlign == "center":
            y -= dh / 2
        elif yAlign == "top":
            y -= dh
    ctx.PushState()
    if flipped:
        s = -scale
    else:
        s = scale
    ctx.Translate(x, y)
    ctx.Scale(scale, s)
    for line in lines:
        ctx.DrawText(line, 0, 0)
        ctx.Translate(0, lineHeight)
    ctx.PopState()


def ellipsePath(ctx, x, y, size):
    halfSize = size / 2
    path = ctx.CreatePath()
    path.AddEllipse(x - halfSize, y - halfSize, size, size)
    return path


def lozengePath(ctx, x, y, size):
    halfSize = size / 2
    path = ctx.CreatePath()
    path.MoveToPoint(x - halfSize, y)
    path.AddLineToPoint(x, y + halfSize)
    path.AddLineToPoint(x + halfSize, y)
    path.AddLineToPoint(x, y - halfSize)
    path.CloseSubpath()
    return path


def squarePath(ctx, x, y, size):
    halfSize = size / 2
    path = ctx.CreatePath()
    path.AddRectangle(x - halfSize, y - halfSize, size, size)
    return path


def trianglePath(ctx, x, y, size, angle):
    thirdSize = size / 3
    path = ctx.CreatePath()
    c, s = cos(angle), sin(angle)
    cSize, sSize = c * size, s * size
    cThirdSize, sThirdSize = c * thirdSize, s * thirdSize
    path.MoveToPoint(
        -cThirdSize - sSize + x, cSize - sThirdSize + y
    )  # -thirdSize, size
    path.AddLineToPoint(
        -cThirdSize + sSize + x, -cSize - sThirdSize + y
    )  # -thirdSize, -size
    path.AddLineToPoint(2 * cThirdSize + x, 2 * sThirdSize + y)  # 2 * thirdSize, 0
    path.CloseSubpath()
    return path


# ----------
# Main sauce
# ----------


def drawCaret(ctx, scale, font):
    master = font.selectedMaster
    ctx.PushState()
    ctx.SetPen(wx.Pen(wx.Colour(63, 63, 63), scale))
    ctx.SetAntialiasMode(wx.ANTIALIAS_NONE)
    ctx.StrokeLine(0, master.descender, 0, master.ascender)
    ctx.PopState()


def drawGlyphFigure(ctx, glyph, width, height, selectionColor=None):
    captionHeight = 14
    figureHeight = height - captionHeight
    # background
    captionColor = wx.Colour(56, 56, 56)
    glyphColor = glyph.color
    ctx.SetPen(wx.NullPen)
    if glyphColor is not None:
        r, g, b, a = glyphColor
        if (2 * r + 5 * g + b) * (a / 255) <= 1024:
            captionColor = wx.WHITE
        color = wx.Colour(r, g, b, a)
        ctx.SetBrush(wx.Brush(color))
        ctx.DrawRectangle(0, figureHeight, width, captionHeight)
        color.Set(r, g, b, .4 * a)
        ctx.SetBrush(wx.Brush(color))
        ctx.DrawRectangle(0, 0, width, figureHeight)
    if glyph.lastModified is not None:
        ctx.SetBrush(wx.Brush(wx.Colour(216, 216, 216, 120)))
        ctx.DrawRectangle(0, 0, width, height)
    if selectionColor is not None:
        ctx.SetBrush(wx.Brush(selectionColor))
        ctx.DrawRectangle(0, 0, width, height)
    # caption text
    ctx_font = ctx.GetFont()
    ctx.SetFont(ctx_font, captionColor)
    # XXX: elide text
    text = glyph.name
    textW, textH = ctx.GetTextExtent(text)
    ctx.DrawText(
        text, (width - textW) // 2, figureHeight + (captionHeight - textH) // 2 - 2
    )
    # content
    master = glyph._parent.selectedMaster
    layer = glyph.layerForMaster(master)
    descender = master.descender
    scale = .8 * figureHeight / (master.ascender - descender)
    if layer:
        xOffset = (width - (layer.width * scale)) // 2
        yOffset = .04 * height - descender * scale
        ctx.PushState()
        ctx.Clip(0, 0, width, figureHeight)
        ctx.Translate(xOffset, figureHeight - yOffset)
        ctx.Scale(scale, -scale)
        ctx.SetBrush(wx.BLACK_BRUSH)
        ctx.SetPen(wx.BLACK_PEN)
        ctx.FillPath(layer.closedComponentsGraphicsPath, wx.WINDING_RULE)
        ctx.StrokePath(layer.openComponentsGraphicsPath)
        ctx.FillPath(layer.closedGraphicsPath, wx.WINDING_RULE)
        ctx.StrokePath(layer.openGraphicsPath)
        ctx.PopState()
    else:
        # foreground template
        uni = glyph.unicode
        char = chr(int(uni, 16) if uni is not None else 0xFFFD)
        ctx_font.SetPixelSize(wx.Size(0, scale * glyph.font.unitsPerEm))
        ctx.SetFont(ctx_font, wx.Colour(228, 228, 228))
        textWidth, lh, d, _ = ctx.GetFullTextExtent(char)
        xOffset = (width - textWidth) // 2
        yOffset = .04 * height - descender * scale + (lh - d)
        ctx.DrawText(char, xOffset, figureHeight - yOffset)


def drawGrid(ctx, scale, rect, color=None):
    if color is None:
        color = wx.Colour(220, 220, 220)
    xMin, yMin, width, height = rect
    xMax = x = round(xMin + width)
    yMax = y = round(yMin + height)
    xMin, yMin = int(xMin), int(yMin)
    path = ctx.CreatePath()
    while x > xMin:
        path.MoveToPoint(x, yMin)
        path.AddLineToPoint(x, yMax)
        x -= 1
    while y > yMin:
        path.MoveToPoint(xMin, y)
        path.AddLineToPoint(xMax, y)
        y -= 1
    ctx.SetPen(wx.Pen(color, scale))
    ctx.StrokePath(path)


def drawLayerAnchors(ctx, layer, scale, color=None):
    anchors = layer._anchors
    if not anchors:
        return
    if color is None:
        color = wx.Colour(178, 102, 76, 200)
    size = 9 * scale
    selectedSize = 11 * scale
    ctx.SetBrush(wx.Brush(color))
    font = ctx.GetFont()
    font.SetPixelSize(wx.Size(0, 11))
    ctx.SetFont(font, color)
    for anchor in anchors.values():
        x, y, selected = anchor.x, anchor.y, anchor.selected
        if selected:
            size_ = selectedSize
        else:
            size_ = size
        ctx.FillPath(lozengePath(ctx, x, y, size_))
        if selected:
            # TODO: we're using + before we shift to top, ideally this should
            # be abstracted w drawTextAtPoint taking a dy parameter that will
            # offset the drawing region from origin regardless of whether we
            # are aligning to top or bottom.
            y += 6 * scale
            drawTextAtPoint(
                ctx, anchor.name, x, y, scale, xAlign="center", yAlign="top"
            )
            # TODO: draw marks overlay
            # we oughta get mark glyph from unicode db


def drawLayerComponents(ctx, layer, scale, fillColor=None, selectedFillColor=None):
    if fillColor is None:
        fillColor = wx.Colour(90, 90, 90, 135)
    if selectedFillColor is None:
        alpha = fillColor.Alpha() if fillColor.IsOk() else 135
        selectedFillColor = wx.Colour(0, 0, 0, alpha)
    fillBrush = wx.Brush(fillColor)
    selectedFillBrush = wx.Brush(selectedFillColor)
    showSelection, wr = selectedFillColor.IsOk(), wx.WINDING_RULE
    ctx.SetPen(wx.Pen(fillColor, scale))
    for component in layer._components:
        drawSelection = showSelection and component.selected
        if drawSelection:
            ctx.SetBrush(selectedFillBrush)
        else:
            ctx.SetBrush(fillBrush)
        ctx.FillPath(component.closedGraphicsPath, wr)
        ctx.StrokePath(component.openGraphicsPath)
        # origin
        # TODO: make this a parameter, disable on sizes < MinDetails
        if drawSelection:
            x, y = component.origin
            ctx.StrokeLine(x, y + 5 * scale, x, y)
            ctx.StrokeLine(x, y, x + 4.5 * scale, y)


def drawLayerGuidelines(ctx, layer, scale, rect, color=None, masterColor=None):
    if color is None:
        color = wx.Colour(56, 71, 213, 128)
    if masterColor is None:
        masterColor = wx.Colour(255, 51, 51, 128)
    _, _, width, height = rect
    dl = width + height  # > viewport diagonal length
    halfSize = 4 * scale
    size = 2 * halfSize
    master = layer.master
    if master is not None:
        toDraw = ((layer, color), (master, masterColor))
    else:
        toDraw = ((layer, color),)
    for container, color in toDraw:
        brush = wx.Brush(color)
        pen = wx.Pen(color, scale)
        for guideline in container.guidelines:
            x, y = guideline.x, guideline.y
            ax, ay = cos_sin_deg(guideline.angle)
            if guideline.selected:
                r, g, b, _ = color.Get()
                color.Set(r, g, b, 190)
                ctx.SetBrush(wx.Brush(color))
                ctx.SetPen(wx.Pen(color, scale))
            else:
                ctx.SetBrush(brush)
                ctx.SetPen(pen)
            ctx.StrokeLine(
                x - ax * dl, y - ay * dl, x - ax * halfSize, y - ay * halfSize
            )
            ctx.StrokeLine(
                x + ax * halfSize, y + ay * halfSize, x + ax * dl, y + ay * dl
            )
            x -= halfSize
            y -= halfSize
            path = ctx.CreatePath()
            path.AddEllipse(x, y, size, size)
            if guideline.selected:
                ctx.DrawPath(path)
            else:
                ctx.StrokePath(path)


def drawLayerImage(ctx, layer, scale, drawSelection=True, selectionColor=None):
    image = layer.image
    bitmap = None  # XXX: impl
    if bitmap is None:
        return
    if selectionColor is None:
        selectionColor = wx.Colour(145, 170, 196, 155)
    ctx.PushState()
    ctx.SetTransform(ctx.CreateMatrix(*image.transformation))
    ctx.PushState()
    ctx.Translate(0, bitmap.GetHeight())
    ctx.Scale(1, -1)
    ctx.DrawBitmap(0, 0, bitmap)
    ctx.PopState()
    if drawSelection and image.selected:
        ctx.SetPen(wx.Pen(selectionColor, 3.5 * scale))
        ctx.DrawRectangle(bitmap.GetRectangle())
    ctx.PopState()


def drawLayerMetrics(ctx, layer, scale, color=None, zonesColor=None):
    master = layer.master
    if master is None:
        return
    if color is None:
        color = wx.Colour(204, 206, 200)
    if zonesColor is None:
        zonesColor = wx.Colour(236, 209, 215, 100)
    width = layer.width
    if zonesColor.IsOk():
        path = ctx.CreatePath()
        for zone in master.alignmentZones:
            path.AddRectangle(0, zone.position, width, zone.size)
        ctx.SetBrush(wx.Brush(zonesColor))
        ctx.FillPath(path)
    if color.IsOk():
        ascender = master.ascender
        capHeight = master.capHeight
        descender = master.descender
        xHeight = master.xHeight
        path = ctx.CreatePath()
        path.MoveToPoint(0, ascender)
        path.AddLineToPoint(width, ascender)
        path.MoveToPoint(0, capHeight)
        path.AddLineToPoint(width, capHeight)
        path.MoveToPoint(0, xHeight)
        path.AddLineToPoint(width, xHeight)
        path.MoveToPoint(0, 0)
        path.AddLineToPoint(width, 0)
        hi = max(ascender, capHeight)
        path.MoveToPoint(0, hi)
        path.AddLineToPoint(0, descender)
        path.AddLineToPoint(width, descender)
        path.AddLineToPoint(width, hi)
        ctx.PushState()
        ctx.SetAntialiasMode(wx.ANTIALIAS_NONE)
        ctx.SetPen(wx.Pen(color, scale))
        ctx.StrokePath(path)
        ctx.PopState()


def drawLayerPoints(
    ctx,
    layer,
    scale,
    coordinatesColor=None,
    markersColor=None,
    offCurveColor=None,
    onCurveColor=None,
    onCurveSmoothColor=None,
    selectionColor=None,
    backgroundColor=None,
):
    if coordinatesColor is None:
        coordinatesColor = wx.Colour(140, 140, 140, 240)
    if markersColor is None:
        markersColor = wx.Colour(235, 191, 202, 225)
    if offCurveColor is None:
        offCurveColor = wx.Colour(116, 116, 116)
    if onCurveColor is None:
        onCurveColor = wx.Colour(4, 100, 166, 190)
    if onCurveSmoothColor is None:
        onCurveSmoothColor = wx.Colour(41, 172, 118, 190)
    if selectionColor is None:
        selectionColor = wx.Colour(145, 170, 196, 155)
    if backgroundColor is None:
        backgroundColor = wx.WHITE
    otherColor = wx.Colour(140, 140, 140, 240)
    paths = layer._paths
    # points
    if onCurveColor.IsOk():
        master = layer.master
        three = 3 * scale
        four = 4 * scale
        five = 5 * scale
        six = 6 * scale
        seven = 7 * scale
        eight = 8 * scale
        nine = 9 * scale
        ten = 10 * scale
        twelve = 2 * six
        fourteen = 2 * seven
        seventeen = 17 * scale
        twenty = 2 * ten
        notchSize = 1.35 * scale
        handlePath = ctx.CreatePath()
        markerPath = ctx.CreatePath()
        notchPath = ctx.CreatePath()
        pointPath = ctx.CreatePath()
        selectedPath = ctx.CreatePath()
        smoothPath = ctx.CreatePath()
        selectedSmoothPath = ctx.CreatePath()
        offPath = ctx.CreatePath()
        selectedOffPath = ctx.CreatePath()
        for path in paths:
            points = path._points
            # start point
            if len(points) > 1:
                start = points[0]
                if start.type != "move":
                    next_ = start
                    start = points[-1]
                else:
                    next_ = points[1]
                x, y = start.x, start.y
                angle = atan2(next_.y - y, next_.x - x)
                if start.selected:
                    startSize_ = nine
                    if start.smooth:
                        pointPath_ = selectedSmoothPath
                    else:
                        pointPath_ = selectedPath
                else:
                    startSize_ = seven
                    if start.smooth:
                        pointPath_ = smoothPath
                    else:
                        pointPath_ = pointPath
                pointPath_.AddPath(trianglePath(ctx, x, y, startSize_, angle))
            else:
                start = None
            # others
            prev = points[-1]
            breakHandle = path.open
            for point in points:
                isOff = point.type is None
                if not breakHandle and isOff != (prev.type is None):
                    handlePath.MoveToPoint(prev.x, prev.y)
                    handlePath.AddLineToPoint(point.x, point.y)
                breakHandle = False
                if isOff:
                    if point.selected:
                        selectedOffPath.AddEllipse(
                            point.x - four, point.y - four, eight, eight
                        )
                    else:
                        offPath.AddEllipse(point.x - three, point.y - three, six, six)
                else:
                    x, y = point.x, point.y
                    if point.smooth:
                        angle = atan2(y - prev.y, x - prev.x) - .5 * pi
                        cn, sn = cos(angle) * notchSize, sin(angle) * notchSize
                        notchPath.MoveToPoint(x - cn, y - sn)
                        notchPath.AddLineToPoint(x + cn, y + sn)
                        if point is start:
                            continue
                        if point.selected:
                            selectedSmoothPath.AddEllipse(x - five, y - five, ten, ten)
                        else:
                            smoothPath.AddEllipse(x - four, y - four, eight, eight)
                    elif point is not start:
                        if point.selected:
                            selectedPath.AddRectangle(x - four, y - four, eight, eight)
                        else:
                            pointPath.AddRectangle(x - three, y - three, six, six)
                    if master is not None:
                        # TODO: we could add a non-overlapping interval tree
                        # special cased for borders
                        for zone in master.alignmentZones:
                            yMin = zone.position
                            yMax = yMin + zone.size
                            if not (y >= yMin and y <= yMax):
                                continue
                            if yMin > 0 and y == yMin or yMin <= 0 and y == yMax:
                                size = twenty if point.selected else seventeen
                                markerPath.AddPath(lozengePath(ctx, x, y, size))
                            else:
                                if point.selected:
                                    halfSize = seven
                                    size = fourteen
                                else:
                                    halfSize = six
                                    size = twelve
                                markerPath.AddEllipse(
                                    x - halfSize, y - halfSize, size, size
                                )
                prev = point
        # markers
        ctx.SetBrush(wx.Brush(markersColor))
        ctx.SetPen(wx.Pen(wx.Colour(255, 255, 255, 125), scale))
        ctx.DrawPath(markerPath, wx.WINDING_RULE)
        # handles
        ctx.SetPen(wx.Pen(otherColor, scale))
        ctx.StrokePath(handlePath)
        # fill
        ctx.SetBrush(wx.Brush(onCurveColor))
        ctx.FillPath(selectedPath, wx.WINDING_RULE)
        ctx.SetBrush(wx.Brush(onCurveSmoothColor))
        ctx.FillPath(selectedSmoothPath, wx.WINDING_RULE)
        # stroke
        pen = wx.Pen(onCurveColor, 1.2 * scale)
        ctx.SetPen(pen)
        ctx.StrokePath(pointPath)
        pen.SetColour(onCurveSmoothColor)
        ctx.SetPen(pen)
        ctx.StrokePath(smoothPath)
        # notch
        ctx.SetPen(wx.Pen(wx.Colour(68, 68, 68), scale))
        ctx.StrokePath(notchPath)
        # off curves
        ctx.SetBrush(wx.Brush(backgroundColor))
        ctx.SetPen(wx.Pen(offCurveColor, 1.75 * scale))
        ctx.DrawPath(offPath)
        r, g, b, _ = offCurveColor.Get()
        offCurveColor.Set(r, g, b, 190)
        ctx.SetBrush(wx.Brush(offCurveColor))
        ctx.FillPath(selectedOffPath, wx.WINDING_RULE)
    # coordinates
    if coordinatesColor.IsOk():
        # TODO
        # - draw onCurve and segment len
        # - use angles around points to place the text in the clear
        ctx.PushState()
        font = ctx.GetFont()  # wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetPixelSize(wx.Size(0, 10))
        ctx.SetFont(font, otherColor)
        for path in paths:
            for point in path.points:
                if point.type is None:
                    continue
                x = round(point.x, 1)
                try:
                    x = int(x)
                except ValueError:
                    pass
                y = round(point.y, 1)
                try:
                    y = int(y)
                except ValueError:
                    pass
                tx, ty = str(x), str(y)
                ctx.PushState()
                ctx.Translate(point.x, point.y)
                ctx.Scale(scale, -scale)
                w, h = ctx.GetTextExtent(tx)
                ctx.Translate(0, -h - 4)
                ctx.DrawText(ty, 4, 0)
                ctx.DrawText(tx, -w - 4, 0)
                ctx.PopState()
        ctx.PopState()


def drawLayerSelectionBounds(ctx, layer, scale):
    if len(layer.selection) <= 1:
        return
    bounds = layer.selectionBounds
    if bounds is None:
        return
    l, b, r, t = bounds
    # rect
    color = wx.Colour(34, 34, 34, 128)
    ctx.SetBrush(wx.NullBrush)
    pen = wx.Pen(color, scale, wx.PENSTYLE_USER_DASH)
    pen.SetDashes([1, 4])
    ctx.SetPen(pen)
    ctx.DrawRectangle(l, b, r - l, t - b)
    # points
    halfSize = 4 * scale
    size = 2 * halfSize
    path = ctx.CreatePath()
    lx, ly = l - 5 - size, b - 5 - size
    hx, hy = r + 5, t + 5
    dx, dy = r - l, t - b
    if dx and dy:
        path.AddEllipse(lx, ly, size, size)
        path.AddEllipse(lx, hy, size, size)
        path.AddEllipse(hx, hy, size, size)
        path.AddEllipse(hx, ly, size, size)
    if dx:
        midy = b + dy // 2 - halfSize
        path.AddEllipse(lx, midy, size, size)
        path.AddEllipse(hx, midy, size, size)
    if dy:
        midx = l + dx // 2 - halfSize
        path.AddEllipse(midx, hy, size, size)
        path.AddEllipse(midx, ly, size, size)
    ctx.SetBrush(wx.Brush(wx.Colour(255, 255, 255, 120)))
    ctx.SetPen(wx.Pen(wx.Colour(163, 163, 163), scale))
    ctx.DrawPath(path)


# should be drawGlyphTemplate tbh
def drawLayerTemplate(ctx, layer, scale):
    glyph = layer._parent
    if glyph is None or glyph.unicode is None:
        return
    # this could be a builtin
    char = chr(int(glyph.unicode, 16))
    font = layer.font
    height = font.unitsPerEm if font is not None else 1000

    font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    font.SetPixelSize(wx.Size(0, height))
    ctx.SetFont(font, wx.Colour(192, 192, 192, 102))

    textWidth, lh, d, _ = ctx.GetFullTextExtent(char)
    xOffset = .5 * (layer.width - textWidth)
    ctx.PushState()
    ctx.Translate(xOffset, lh - d)
    ctx.Scale(1, -1)
    ctx.DrawText(char, 0, 0)
    ctx.PopState()


def drawLayerTextMetrics(ctx, layer, scale, color=None):
    master = layer.master
    if master is None:
        return
    if color is None:
        color = wx.Colour(204, 206, 200)
    width = layer.width
    if color.IsOk():
        ascender = master.ascender
        capHeight = master.capHeight
        descender = master.descender
        hi = max(ascender, capHeight)
        nh = nw = 4 * scale
        ctx.PushState()
        ctx.SetAntialiasMode(wx.ANTIALIAS_NONE)
        ctx.SetPen(wx.Pen(color, scale))
        ctx.StrokeLine(0, descender - nh, 0, descender + nh)
        ctx.StrokeLine(0, -nh, 0, nh)
        ctx.StrokeLine(0, hi - nh, 0, hi)
        ctx.StrokeLine(width, descender - nh, width, descender + nh)
        ctx.StrokeLine(width, -nh, width, nh)
        ctx.StrokeLine(width, hi - nh, width, hi)
        #
        ctx.StrokeLine(0, descender, nw, descender)
        ctx.StrokeLine(0, 0, nw, 0)
        ctx.StrokeLine(0, hi, nw, hi)
        ctx.StrokeLine(width - nw, descender, width, descender)
        ctx.StrokeLine(width - nw, 0, width, 0)
        ctx.StrokeLine(width - nw, hi, width, hi)
        ctx.PopState()
        #
        ctx.PushState()
        font = ctx.GetFont()
        font.SetPointSize(8 * scale)
        ctx.SetFont(font, color)
        ctx.Scale(1, -1)
        ph = 3 * scale
        ph = pw = 4 * scale
        leftMargin = layer.leftMargin
        if leftMargin is not None:
            text = str(round(leftMargin))
            ctx.DrawText(text, pw, ph - descender)
        text = str(round(layer.width))
        w, _ = ctx.GetTextExtent(text)
        ctx.DrawText(text, .5 * (layer.width - w), ph - descender)
        rightMargin = layer.rightMargin
        if rightMargin is not None:
            text = str(round(rightMargin))
            w, _ = ctx.GetTextExtent(text)
            ctx.DrawText(text, layer.width - w - pw, ph - descender)
        ctx.PopState()
