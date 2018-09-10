from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont
from trufont.objects.layoutEngine import LayoutEngine
from trufont.util.canvasDelete import filterSelection
from trufont.util.drawing import CreateMatrix, CreatePath
from tfont.objects import Component, Font, Layer, Path


def componentClosedGraphicsPathFactory(component):
    graphicsPath = CreatePath()
    graphicsPath.AddPath(component.layer.closedGraphicsPath)
    graphicsPath.Transform(
        CreateMatrix(*component.transformation))
    return graphicsPath


def componentOpenGraphicsPathFactory(component):
    graphicsPath = CreatePath()
    graphicsPath.AddPath(component.layer.openGraphicsPath)
    graphicsPath.Transform(
        CreateMatrix(*component.transformation))
    return graphicsPath


def fontLayoutEngineFactory(font):
    # this could be font.buildFeatures() although we might
    # want a pluggable generator so one can write custom codegen...
    features = "\n".join(
        [str(featHdr) for featHdr in font.featureHeaders] +
        [str(featCls) for featCls in font.featureClasses] +
        [str(feature) for feature in font.features])
    glyphOrder = [glyph.name for glyph in font.glyphs]
    tables = {}
    # TODO: no kernWriter, but markWriter?
    if features.strip():
        otf = TTFont()
        otf.setGlyphOrder(glyphOrder)
        addOpenTypeFeaturesFromString(otf, features)
        for name in ("GDEF", "GSUB", "GPOS"):
            if name in otf:
                tables[name] = otf[name].compile(otf)
    return LayoutEngine(font, tables)


def layerClosedComponentsGraphicsPathFactory(layer):
    graphicsPath = CreatePath()
    for component in layer._components:
        graphicsPath.AddPath(component.closedGraphicsPath)
    return graphicsPath


def layerClosedGraphicsPathFactory(layer):
    graphicsPath = CreatePath()
    for path in layer._paths:
        if not path.open:
            graphicsPath.AddPath(path.graphicsPath)
    return graphicsPath


def layerOpenComponentsGraphicsPathFactory(layer):
    graphicsPath = CreatePath()
    for component in layer._components:
        graphicsPath.AddPath(component.openGraphicsPath)
    return graphicsPath


def layerOpenGraphicsPathFactory(layer):
    graphicsPath = CreatePath()
    for path in layer._paths:
        if path.open:
            graphicsPath.AddPath(path.graphicsPath)
    return graphicsPath


def pathGraphicsPathFactory(path):
    graphicsPath = CreatePath()
    points = path._points
    if not points:
        return graphicsPath
    start = points[0]
    open_ = skip = start.type == "move"
    if open_:
        graphicsPath.MoveToPoint(start.x, start.y)
    else:
        start = points[-1]
        assert start.type is not None
        graphicsPath.MoveToPoint(start.x, start.y)
    stack = []
    for point in points:
        if skip:
            skip = False
        elif point.type == "line":
            assert not stack
            graphicsPath.AddLineToPoint(point.x, point.y)
        else:
            stack.append(point.x)
            stack.append(point.y)
            if point.type == "curve":
                graphicsPath.AddCurveToPoint(*stack)
                stack = []
    if not open_:
        graphicsPath.CloseSubpath()
    return graphicsPath


def registerAllFactories():
    Component.closedGraphicsPathFactory = componentClosedGraphicsPathFactory
    Component.openGraphicsPathFactory = componentOpenGraphicsPathFactory
    Font.layoutEngineFactory = fontLayoutEngineFactory
    Layer.closedComponentsGraphicsPathFactory = \
        layerClosedComponentsGraphicsPathFactory
    Layer.closedGraphicsPathFactory = \
        layerClosedGraphicsPathFactory
    Layer.openComponentsGraphicsPathFactory = \
        layerOpenComponentsGraphicsPathFactory
    Layer.openGraphicsPathFactory = \
        layerOpenGraphicsPathFactory
    Layer.selectedPathsFactory = lambda layer: filterSelection(layer._paths)
    Path.graphicsPathFactory = pathGraphicsPathFactory
