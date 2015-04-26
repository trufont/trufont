from PyQt5.QtCore import QPointF, QSize, Qt
from PyQt5.QtGui import QBrush, QFont, QFontMetrics, QPainter, QPainterPath
from PyQt5.QtWidgets import QApplication, QComboBox, QGridLayout, QWidget

class RenderArea(QWidget):
    def __init__(self, cellWidth, cellHeight, parent=None):
        super(RenderArea, self).__init__(parent)

        self.width_ = cellWidth
        self.height_ = cellHeight
#        newFont = self.font()
#        newFont.setPixelSize(12)
#        self.setFont(newFont)

#        fontMetrics = QFontMetrics(newFont)
#        self.xBoundingRect = fontMetrics.boundingRect("x")
#        self.yBoundingRect = fontMetrics.boundingRect("y")
        self.shape = QPainterPath()
#        self.operations = []

    def setShape(self, shape):
        self.shape = shape
        self.update()

    def minimumSizeHint(self):
        return QSize(100, 100)

    def sizeHint(self):
        return QSize(self.width_, self.height_)

    # Draw a QPainterPath stored in `self.shape`.
    def oldPaint(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Be cartesian
        painter.translate(event.rect().bottomLeft())
        painter.scale(1.0, -1.0)
        
        painter.fillRect(event.rect(), QBrush(Qt.white))

        painter.save()
        self.drawShape(painter)
        painter.restore()

        #self.drawOutline(painter)
        #self.drawCoordinates(painter)

    def newPaint(self, event):
        _, _, width, height = event.rect().getRect()
        painter = glyph.getRepresentation("defconQt.QPainterPath", width=width, height=height)

    def paintEvent(self, event):
        #oldPaint(self, event)
        pass

    def drawCoordinates(self, painter):
        #raise NotImplementedError
        painter.setPen(Qt.red)

        painter.drawLine(0, 0, 50, 0)
        painter.drawLine(48, -2, 50, 0)
        painter.drawLine(48, 2, 50, 0)
        #painter.drawText(60 - self.xBoundingRect.width() / 2,
        #                 0 + self.xBoundingRect.height() / 2, "x")

        painter.drawLine(0, 0, 0, 50)
        painter.drawLine(-2, 48, 0, 50)
        painter.drawLine(2, 48, 0, 50)
        #painter.drawText(0 - self.yBoundingRect.width() / 2,
        #                 60 + self.yBoundingRect.height() / 2, "y")

    '''
    Debug method – paints a single glyph. drawGlyphCell() is the path forward.
    '''
    def drawGlyph(self, font, glyphId): #, width, height
        #glyph = font[glyphId]

        # TODO: need to write the cell repr
        #rep = glyph.getRepresentation("defconQt.QPainterPath", width=width, height=height)
        '''#TODO: adapt glyph size to window size
        if not rep.isEmpty():
            glyphWidth = glyph.width
        '''
        #self.setShape(rep)
        self.glyph_ = font[glyphId]
        self.update()
    
    def drawGlyphCell(self, glyph, font):
        rep = font[glyph].getRepresentation("defconQt.GlyphCell", width=self.width_, height=self.height_)
        self.setShape(rep)
        #GlyphCellFactory(glyph, font, self.width_, self.height_)

    #def drawOutline(self, painter):
    #    painter.setPen(Qt.darkGreen)
    #    painter.setPen(Qt.DashLine)
    #    painter.setBrush(Qt.NoBrush)
    #    painter.drawRect(0, 0, 100, 100)

    def drawShape(self, painter):
        #painter.drawPath(self.shape)
        painter.fillPath(self.shape, Qt.blue)


class Window(QWidget):

    def __init__(self, glyphs=[]):
        super(Window, self).__init__()
        
        self._glyphs = glyphs
        self._cellWidth = 200
        self._cellHeight = 200
        self._cnt = 4 # till it shows the whole font
        self.setWindowTitle("Font View")

        self.layoutConstruction(self._cnt)

        
        #self.preloadGlyphCellImages()

    def layoutConstruction(self, cnt):
        layout = QGridLayout()
        #layout.setHorizontalSpacing(0)
        #layout.setVerticalSpacing(0)
        
        self.glyphsGrid = list(range(cnt))
        for i in range(cnt):
            self.glyphsGrid[i] = RenderArea(self._cellWidth, self._cellHeight)
            layout.addWidget(self.glyphsGrid[i], 0, i)
        self.setLayout(layout)

    '''
    def preloadGlyphCellImages(self):
        representationName = self._cellRepresentationName
        representationArguments = self._cellRepresentationArguments
        cellWidth = self._cellWidth
        cellHeight = self._cellHeight
        for glyph in self._glyphs:
            glyph.getRepresentation(representationName, width=cellWidth, height=cellHeight, **representationArguments)
        self.setLayout(layout)
    '''

    def setGlyphs_(self, glyphs):
        self._glyphs = glyphs
    #    self.glyphsGrid.setGlyphs(glyphs)


    '''
    Debug method.
    '''
    def setGlyph(self, font, glyphId):
        self.glyphsGrid[0].drawGlyph(font, glyphId, self._cellWidth, self._cellHeight)

    def shapeSelected(self, index):
        shape = self.shapes[index]
        self.glyphsGrid.setShape(shape)
        for i in range(Window.NumTransformedAreas):
            self.transformedRenderAreas[i].setShape(shape)
