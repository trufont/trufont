from defcon.objects.glyph import addRepresentationFactory
#from defconQt.representationFactories.qPainterPathFactory import QPainterPathFactory
###
from fontTools.pens.qtPen import QtPen

def QPainterPathFactory(glyph, font):
    pen = QtPen(font)
    glyph.draw(pen)
    return pen.path
###
#from defconQt.representationFactories.glyphCellFactory import GlyphCellFactory
###
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QColor, QPainter, QPixmap

GlyphCellHeaderHeight = 14
GlyphCellMinHeightForHeader = 40

# 1 is white
cellHeaderBaseColor = QColor.fromRgb(153, 153, 153).setAlphaF(.4)
#NSColor.colorWithCalibratedWhite_alpha_(.6, .4)
cellHeaderHighlightColor = QColor.fromRgb(178, 178, 178).setAlphaF(.4)
#NSColor.colorWithCalibratedWhite_alpha_(.7, .4)
cellHeaderSelectionColor = QColor.fromRgbF(.2, .3, .7, .15)
#NSColor.colorWithCalibratedRed_green_blue_alpha_(.2, .3, .7, .15)
cellHeaderLineColor = QColor.fromRgb(0, 0, 0).setAlphaF(.2)
#NSColor.colorWithCalibratedWhite_alpha_(0, .2)
cellHeaderHighlightLineColor = QColor.fromRgb(25, 25, 25).setAlphaF(.5)
#NSColor.colorWithCalibratedWhite_alpha_(1, .5)
cellMetricsLineColor = QColor.fromRgb(0, 0, 0).setAlphaF(.08)
#NSColor.colorWithCalibratedWhite_alpha_(0, .08)
cellMetricsFillColor = QColor.fromRgb(0, 0, 0).setAlphaF(.08)
#NSColor.colorWithCalibratedWhite_alpha_(0, .08)



def GlyphCellFactory(glyph, font, width, height, drawHeader=False, drawMetrics=False):
    obj = GlyphCellFactoryDrawingController(glyph=glyph, font=font, width=width, height=height, drawHeader=drawHeader, drawMetrics=drawMetrics)
    return obj.getImage()


class GlyphCellFactoryDrawingController(object):

    """
    This draws the cell with the layers stacked in this order:
    ------------------
    header text
    ------------------
    header background
    ------------------
    foreground
    ------------------
    glyph
    ------------------
    vertical metrics
    ------------------
    horizontal metrics
    ------------------
    background
    ------------------

    Subclasses may override the layer drawing methods to customize
    the appearance of cells.
    """

    def __init__(self, glyph, font, width, height, drawHeader=False, drawMetrics=False):
        self.glyph = glyph
        self.font = font
        self.width = width
        self.height = height
        self.bufferPercent = .2
        self.shouldDrawHeader = drawHeader
        self.shouldDrawMetrics = drawMetrics

        self.headerHeight = 0
        if drawHeader:
            self.headerHeight = GlyphCellHeaderHeight
        availableHeight = (height - self.headerHeight) * (1.0 - (self.bufferPercent * 2))
        self.buffer = height * self.bufferPercent
        self.scale = availableHeight / font.info.unitsPerEm
        self.xOffset = (width - (glyph.width * self.scale)) / 2
        self.yOffset = abs(font.info.descender * self.scale) + self.buffer

    def getImage(self):
        image = QPixmap(self.width, self.height) #NSImage.alloc().initWithSize_((self.width, self.height))
        painter = QPainter(image).setRenderHint(QPainter.Antialiasing)
        #image.setFlipped_(True)
        #image.lockFocus()
        #context = NSGraphicsContext.currentContext()
        
        # Below is probably wrong… find out about (x,y) orientation and plane translation that might affect this
        # Qt is top-left by default while AppKit is bottom-left – Qt translation+scale affects text display
        bodyRect = QRect(0, self.headerHeight, self.width, self.height-self.headerHeight)
        headerRect = QRect(0, 0, self.width, self.headerHeight)
        #bodyRect = ((0, 0), (self.width, self.height-self.headerHeight))
        #headerRect = ((0, -self.height+self.headerHeight), (self.width, self.headerHeight))
        # background
        painter.save()
        #context.saveGraphicsState()
        painter.translate(0, self.height-self.headerHeight)
        painter.scale(1.0, -1.0)
        #bodyTransform = NSAffineTransform.transform()
        #bodyTransform.translateXBy_yBy_(0, self.height-self.headerHeight)
        #bodyTransform.scaleXBy_yBy_(1.0, -1.0)
        #bodyTransform.concat()
        self.drawCellBackground(painter, bodyRect)
        painter.restore()
        #context.restoreGraphicsState()
        # glyph
        if self.shouldDrawMetrics:
            self.drawCellHorizontalMetrics(painter, bodyRect)
            self.drawCellVerticalMetrics(painter, bodyRect)
        #context.saveGraphicsState()
        painter.save()
        # clip against background only
        painter.setClipRect(QRect(0, 0, self.width, self.height-self.headerHeight))
        #NSBezierPath.clipRect_()
        painter.translate(self.xOffset, self.yOffset)
        painter.scale(self.scale, self.scale)
        #glyphTransform = NSAffineTransform.transform()
        #glyphTransform.translateXBy_yBy_(self.xOffset, self.yOffset)
        #glyphTransform.scaleBy_(self.scale)
        #glyphTransform.concat()
        self.drawCellGlyph(painter)
        painter.restore()
        #context.restoreGraphicsState()
        # foreground
        painter.save()
        #context.saveGraphicsState()
        #bodyTransform.concat() #why this lonely here?
        self.drawCellForeground(painter, bodyRect)
        painter.restore()
        #context.restoreGraphicsState()
        # header
        if self.shouldDrawHeader:
            painter.save()
            #context.saveGraphicsState()
            painter.translate(0, self.headerHeight)
            painter.scale(1.0, -1.0)
            #headerTransform = NSAffineTransform.transform()
            #headerTransform.translateXBy_yBy_(0, self.headerHeight)
            #headerTransform.scaleXBy_yBy_(1.0, -1.0)
            #headerTransform.concat()
            self.drawCellHeaderBackground(painter, headerRect)
            self.drawCellHeaderText(painter, headerRect)
            painter.restore()
            #context.restoreGraphicsState()
        # done
        #image.unlockFocus()

        return painter#image

    def drawCellBackground(self, painter, rect):
        pass

    def drawCellHorizontalMetrics(self, painter, rect):
        (xMin, yMin, width, height) = rect.getRect()
        glyph = self.glyph
        font = self.font
        scale = self.scale
        yOffset = self.yOffset
        path = QPainterPath()
        #path = NSBezierPath.bezierPath()
        lines = set((0, font.info.descender, font.info.xHeight, font.info.capHeight, font.info.ascender))
        for y in lines:
            y = round((y * scale) + yMin + yOffset) - .5
            path.moveTo(xMin, y)
            path.lineTo(xMin + width, y)
        #cellMetricsLineColor.set()
        stroke = QPainterPathStroker().createStroke(path)
        stroke.setWidth(1.0)

        painter.save()
        painter.setPen(cellMetricsLineColor)
        painter.drawPath(stroke)
        painter.restore()
        #path.stroke()

    def drawCellVerticalMetrics(self, painter, rect):
        (xMin, yMin, width, height) = rect.getRect()
        glyph = self.glyph
        scale = self.scale
        xOffset = self.xOffset
        left = round((0 * scale) + xMin + xOffset) - .5
        right = round((glyph.width * scale) + xMin + xOffset) - .5

        # Does this replicate functionality properly? Need to check that…
        painter.fillRect((xMin, yMin, left - xMin, height), cellMetricsFillColor)
        painter.fillRect((xMin + right, yMin, width - xMin + right, height), cellMetricsFillColor)
        #rects = [
        #    ((xMin, yMin), (left - xMin, height)),
        #    ((xMin + right, yMin), (width - xMin + right, height))
        #]
        #cellMetricsFillColor.set()
        #NSRectFillListUsingOperation(rects, len(rects), NSCompositeSourceOver)

    def drawCellGlyph(self, painter):
        #NSColor.blackColor().set()
        painter.fillPath(self.glyph.getRepresentation("defconQt.QPainterPath"), Qt.black)

    def drawCellForeground(self, painter, rect):
        pass

    def drawCellHeaderBackground(self, painter, rect):
        (xMin, yMin, width, height) = rect.getRect()
        # background
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0, cellHeaderHighlightColor)
        gradient.setColorAt(1, cellHeaderBaseColor)
        painter.save()
        painter.rotate(90)
        painter.fillRect(rect, gradient)
        painter.restore()
        #try:
        #    gradient = NSGradient.alloc().initWithColors_([cellHeaderHighlightColor, cellHeaderBaseColor])
        #    gradient.drawInRect_angle_(rect, 90)
        #except NameError:
        #    cellHeaderBaseColor.set()
        #    NSRectFill(rect)
        # left and right line
        sizePath = QPainterPath()
        sizePath.moveTo(xMin + .5, yMin)
        sizePath.lineTo(xMin + .5, yMin + height)
        sizePath.moveTo(xMin + width - 1.5, yMin)
        sizePath.lineTo(xMin + width - 1.5, yMin + height)
        sizeStroke = QPainterPathStroker().createStroke(path)
        sizeStroke.setWidth(1.0)
        #painter.save()
        painter.setPen(cellHeaderHighlightLineColor)
        painter.drawPath(sizeStroke)
        #painter.restore()
        #cellHeaderHighlightLineColor.set()
        #sizePath = NSBezierPath.bezierPath()
        #sizePath.moveToPoint_((xMin + .5, yMin))
        #sizePath.lineToPoint_((xMin + .5, yMin + height))
        #sizePath.moveToPoint_((xMin + width - 1.5, yMin))
        #sizePath.lineToPoint_((xMin + width - 1.5, yMin + height))
        #sizePath.setLineWidth_(1.0)
        #sizePath.stroke()
        # bottom line
        bottomPath = QPainterPath()
        bottomPath.moveTo(xMin, yMin + height - .5)
        bottomPath.lineTo(xMin + width, yMin + height - .5)
        #cellHeaderLineColor.set()
        #bottomPath = NSBezierPath.bezierPath()
        #bottomPath.moveToPoint_((xMin, yMin + height - .5))
        #bottomPath.lineToPoint_((xMin + width, yMin + height - .5))
        #bottomPath.setLineWidth_(1.0)
        #bottomPath.stroke()
        bottomStroke = QPainterPathStroker().createStroke(path)
        bottomStroke.setWidth(1.0)
        #painter.save()
        painter.setPen(cellHeaderLineColor)
        painter.drawPath(bottomStroke)
        #painter.restore()

    def drawCellHeaderText(self, painter, rect):
        textColor = QColor.fromRgbF(.22, .22, .27, 1.0)
        #NSColor.colorWithCalibratedRed_green_blue_alpha_(.22, .22, .27, 1.0)

        # TODO: no shadow for now, need to use QGraphicsDropShadowEffect but tricky to impl
        #painter.save()
        painter.setPen(textColor)
        painter.setFont(QFont(QFont.defaultFamily(), 10))
        painter.drawText(rect, Qt.AlignCenter, self.glyph.name);
        #painter.restore()

        #paragraph = NSMutableParagraphStyle.alloc().init()
        #paragraph.setAlignment_(NSCenterTextAlignment)
        #paragraph.setLineBreakMode_(NSLineBreakByTruncatingMiddle)
        #shadow = NSShadow.alloc().init()
        #shadow.setShadowColor_(NSColor.whiteColor())
        #shadow.setShadowOffset_((0, 1))
        #shadow.setShadowBlurRadius_(1)
        #attributes = {
        #    NSFontAttributeName : NSFont.systemFontOfSize_(10.0),
        #    NSForegroundColorAttributeName : NSColor.colorWithCalibratedRed_green_blue_alpha_(.22, .22, .27, 1.0),
        #    NSParagraphStyleAttributeName : paragraph,
        #    NSShadowAttributeName : shadow
        #}
        #text = NSAttributedString.alloc().initWithString_attributes_(self.glyph.name, attributes)
        #text.drawInRect_(rect)

###

_factories = {
    "defconQt.QPainterPath" : QPainterPathFactory,
    "defconQt.GlyphCell" : GlyphCellFactory,
}

def registerAllFactories():
    for name, factory in _factories.items():
        addRepresentationFactory(name, factory)