from PyQt5.QtCore import QFile, QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPixmap, QPen
from PyQt5.QtWidgets import (QActionGroup, QApplication, QFileDialog,
        QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
        QMainWindow, QMenu, QMessageBox, QWidget)
from PyQt5.QtOpenGL import QGL, QGLFormat, QGLWidget
from PyQt5.QtSvg import QGraphicsSvgItem


class MainGfxWindow(QMainWindow):
    def __init__(self, font=None, glyph=None, parent=None):
        super(MainGfxWindow, self).__init__(parent)

        self.currentPath = ''

        self.view = SvgView()
        self.view.setGlyph(font, glyph)

        fileMenu = QMenu("&File", self)
        openAction = fileMenu.addAction("&Open...")
        openAction.setShortcut("Ctrl+O")
        quitAction = fileMenu.addAction("E&xit")
        quitAction.setShortcut("Ctrl+Q")

        self.menuBar().addMenu(fileMenu)

        viewMenu = QMenu("&View", self)
        self.backgroundAction = viewMenu.addAction("&Background")
        self.backgroundAction.setEnabled(False)
        self.backgroundAction.setCheckable(True)
        self.backgroundAction.setChecked(False)
        self.backgroundAction.toggled.connect(self.view.setViewBackground)

        self.outlineAction = viewMenu.addAction("&Outline")
        self.outlineAction.setEnabled(False)
        self.outlineAction.setCheckable(True)
        self.outlineAction.setChecked(True)
        self.outlineAction.toggled.connect(self.view.setViewOutline)

        self.menuBar().addMenu(viewMenu)

        rendererMenu = QMenu("&Renderer", self)
        self.nativeAction = rendererMenu.addAction("&Native")
        self.nativeAction.setCheckable(True)
        self.nativeAction.setChecked(True)

        if QGLFormat.hasOpenGL():
            self.glAction = rendererMenu.addAction("&OpenGL")
            self.glAction.setCheckable(True)

        self.imageAction = rendererMenu.addAction("&Image")
        self.imageAction.setCheckable(True)

        if QGLFormat.hasOpenGL():
            rendererMenu.addSeparator()
            self.highQualityAntialiasingAction = rendererMenu.addAction("&High Quality Antialiasing")
            self.highQualityAntialiasingAction.setEnabled(False)
            self.highQualityAntialiasingAction.setCheckable(True)
            self.highQualityAntialiasingAction.setChecked(False)
            self.highQualityAntialiasingAction.toggled.connect(self.view.setHighQualityAntialiasing)

        rendererGroup = QActionGroup(self)
        rendererGroup.addAction(self.nativeAction)

        if QGLFormat.hasOpenGL():
            rendererGroup.addAction(self.glAction)

        rendererGroup.addAction(self.imageAction)

        self.menuBar().addMenu(rendererMenu)

        openAction.triggered.connect(self.openFile)
        quitAction.triggered.connect(QApplication.instance().quit)
        rendererGroup.triggered.connect(self.setRenderer)

        self.setCentralWidget(self.view)
        self.setWindowTitle("Glyph view")

    def openFile(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Open SVG File",
                    self.currentPath, "SVG files (*.svg *.svgz *.svg.gz)")

        if path:
            svg_file = QFile(path)
            if not svg_file.exists():
                QMessageBox.critical(self, "Open SVG File",
                        "Could not open file '%s'." % path)

                self.outlineAction.setEnabled(False)
                self.backgroundAction.setEnabled(False)
                return

            self.view.openFile(svg_file)

            if not path.startswith(':/'):
                self.currentPath = path
                self.setWindowTitle("%s - SVGViewer" % self.currentPath)

            self.outlineAction.setEnabled(True)
            self.backgroundAction.setEnabled(True)

            self.resize(self.view.sizeHint() + QSize(80, 80 + self.menuBar().height()))

    def setRenderer(self, action):
        if QGLFormat.hasOpenGL():
            self.highQualityAntialiasingAction.setEnabled(False)

        if action == self.nativeAction:
            self.view.setRenderer(SvgView.Native)
        elif action == self.glAction:
            if QGLFormat.hasOpenGL():
                self.highQualityAntialiasingAction.setEnabled(True)
                self.view.setRenderer(SvgView.OpenGL)
        elif action == self.imageAction:
            self.view.setRenderer(SvgView.Image)


class SvgView(QGraphicsView):
    Native, OpenGL, Image = range(3)

    def __init__(self, parent=None):
        super(SvgView, self).__init__(parent)

        self.renderer = SvgView.Native
        self.svgItem = None
        self.backgroundItem = None
        self.outlineItem = None
        self.image = QImage()
        self._glyph = None

        self.setScene(QGraphicsScene(self))
        # XXX: this should allow us to move the view but doesn't happen...
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.setRenderHint(QPainter.Antialiasing)

        # Prepare background check-board pattern.
        tilePixmap = QPixmap(64, 64)
        tilePixmap.fill(Qt.white)
        tilePainter = QPainter(tilePixmap)
        color = QColor(220, 220, 220)
        tilePainter.fillRect(0, 0, 32, 32, color)
        tilePainter.fillRect(32, 32, 32, 32, color)
        tilePainter.end()

        self.setBackgroundBrush(QBrush(tilePixmap))

    def drawBackground(self, p, rect):
        p.save()
        p.resetTransform()
        p.drawTiledPixmap(self.viewport().rect(),
                self.backgroundBrush().texture())
        p.restore()
        
    def addOutlines(self):
        s = self.scene()
        #painter = QPainter(self.viewport())
        #painter.translate(0, self.height()*(1+self._font.info.descender/self._font.info.unitsPerEm))
        #painter.scale(1, -1)
        #painter.setRenderHint(QPainter.Antialiasing)
        # outlines
        path = self._glyph.getRepresentation("defconQt.QPainterPath")
        s.addPath(path, brush=QBrush(Qt.black))
        # components
        '''
        path = self._glyph.getRepresentation("defconAppKit.OnlyComponentsNSBezierPath")
        self._componentFillColor.set()
        path.fill()
        '''

    def addPoints(self):
        # work out appropriate sizes and
        # skip if the glyph is too small
        s = self.scene()
        #painter = QPainter(self.viewport())
        #painter.translate(0, self.height()*(1+self._font.info.descender/self._font.info.unitsPerEm))
        #painter.scale(1, -1)
        #painter.setRenderHint(QPainter.Antialiasing)
        pointSize = 1000#self._impliedPointSize
        if pointSize > 550:
            startPointSize = 21
            offCurvePointSize = 5
            onCurvePointSize = 6
            onCurveSmoothPointSize = 7
        elif pointSize > 250:
            startPointSize = 15
            offCurvePointSize = 3
            onCurvePointSize = 4
            onCurveSmoothPointSize = 5
        elif pointSize > 175:
            startPointSize = 9
            offCurvePointSize = 1
            onCurvePointSize = 2
            onCurveSmoothPointSize = 3
        else:
            return
        if pointSize > 250:
            coordinateSize = 9
        else:
            coordinateSize = 0
        # use the data from the outline representation
        outlineData = self._glyph.getRepresentation("defconQt.OutlineInformation")
        points = []
        # start point
        if self._showOnCurvePoints and outlineData["startPoints"]:
            startWidth = startHeight = self.roundPosition(startPointSize)# * self._inverseScale)
            startHalf = startWidth / 2.0
            path = QPainterPath()
            for point, angle in outlineData["startPoints"]:
                x, y = point
                if angle is not None:
                    path.moveTo(x, y)
                    path.arcTo(x-startHalf, y-startHalf, 2*startHalf, 2*startHalf, angle-90, -180)
                    #path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
                    #    (x, y), startHalf, angle-90, angle+90, True)
                    path.closeSubpath()
                else:
                    path.addEllipse(x-startHalf, y-startHalf, startWidth, startHeight)
            #self._startPointColor.set()
            #path.fill()
            #painter.fillPath(path, Qt.blue)
            s.addPath(path, brush=QBrush(Qt.blue))
        # off curve
        if self._showOffCurvePoints and outlineData["offCurvePoints"]:
            # lines
            path = QPainterPath()
            for point1, point2 in outlineData["bezierHandles"]:
                path.moveTo(*point1)
                path.lineTo(*point2)
            #self._bezierHandleColor.set()
            #path.setLineWidth_(1.0 * self._inverseScale)
            #painter.setPen(QPen(Qt.black, 1.0 * self._inverseScale))
            # painter.drawPath(path)
            s.addPath(path, Qt.black)
            # points
            offWidth = offHeight = self.roundPosition(offCurvePointSize)# * self._inverseScale)
            offHalf = offWidth / 2.0
            path = QPainterPath()
            for point in outlineData["offCurvePoints"]:
                x, y = point["point"]
                points.append((x, y))
                x = self.roundPosition(x - offHalf)
                y = self.roundPosition(y - offHalf)
                path.addEllipse(x, y, offWidth, offHeight)
            #path.setLineWidth_(3.0#* self._inverseScale)
            #self._pointStrokeColor.set()
            #s.addPath(path, QPen(QBrush(Qt.darkGray), 3.0))
            #self._backgroundColor.set()
            s.addPath(path, brush=QBrush(Qt.green))
            #self._pointColor.set()
            #path.setLineWidth_(1.0 * self._inverseScale)
            s.addPath(path, QPen(QBrush(Qt.black), 1.0))
            #path.stroke()
        # on curve
        if self._showOnCurvePoints and outlineData["onCurvePoints"]:
            width = height = self.roundPosition(onCurvePointSize)# * self._inverseScale)
            half = width / 2.0
            smoothWidth = smoothHeight = self.roundPosition(onCurveSmoothPointSize)# * self._inverseScale)
            smoothHalf = smoothWidth / 2.0
            path = QPainterPath()
            for point in outlineData["onCurvePoints"]:
                x, y = point["point"]
                points.append((x, y))
                if point["smooth"]:
                    x = self.roundPosition(x - smoothHalf)
                    y = self.roundPosition(y - smoothHalf)
                    path.addEllipse(x, y, smoothWidth, smoothHeight)
                else:
                    x = self.roundPosition(x - half)
                    y = self.roundPosition(y - half)
                    path.addRect(x, y, width, height)
            #self._pointStrokeColor.set()
            #path.setLineWidth_(3.0 * self._inverseScale)
            # painter.drawPath(path)
            s.addPath(path, Qt.black)
            #self._pointColor.set()
            # painter.fillPath(path, Qt.red)
            s.addPath(path, brush=QBrush(Qt.red))
        # text
        """
        if self._showPointCoordinates and coordinateSize:
            fontSize = 9 * self._inverseScale
            attributes = {
                NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
                NSForegroundColorAttributeName : self._pointCoordinateColor
            }
            for x, y in points:
                posX = x
                posY = y
                x = round(x, 1)
                if int(x) == x:
                    x = int(x)
                y = round(y, 1)
                if int(y) == y:
                    y = int(y)
                text = "%d  %d" % (x, y)
                self._drawTextAtPoint(text, attributes, (posX, posY), 3)
        """

    def openPath(self, path):
        if path is None: return
        s = self.scene()
        s.clear()
        self.resetTransform()
        #self.scale(1, -1)
        
        #s.addPath(path, brush=QBrush(Qt.gray))
        #s.setSceneRect(path.boundingRect().adjusted(-10, -10, 10, 10))

    def openFile(self, svg_file):
        if not svg_file.exists():
            return

        s = self.scene()

        if self.backgroundItem:
            drawBackground = self.backgroundItem.isVisible()
        else:
            drawBackground = False

        if self.outlineItem:
            drawOutline = self.outlineItem.isVisible()
        else:
            drawOutline = True

        s.clear()
        self.resetTransform()

        self.svgItem = QGraphicsSvgItem(svg_file.fileName())
        self.svgItem.setFlags(QGraphicsItem.ItemClipsToShape)
        self.svgItem.setCacheMode(QGraphicsItem.NoCache)
        self.svgItem.setZValue(0)

        self.backgroundItem = QGraphicsRectItem(self.svgItem.boundingRect())
        self.backgroundItem.setBrush(Qt.white)
        self.backgroundItem.setPen(QPen(Qt.NoPen))
        self.backgroundItem.setVisible(drawBackground)
        self.backgroundItem.setZValue(-1)

        self.outlineItem = QGraphicsRectItem(self.svgItem.boundingRect())
        outline = QPen(Qt.black, 2, Qt.DashLine)
        outline.setCosmetic(True)
        self.outlineItem.setPen(outline)
        self.outlineItem.setBrush(QBrush(Qt.NoBrush))
        self.outlineItem.setVisible(drawOutline)
        self.outlineItem.setZValue(1)

        s.addItem(self.backgroundItem)
        s.addItem(self.svgItem)
        s.addItem(self.outlineItem)

        s.setSceneRect(self.outlineItem.boundingRect().adjusted(-10, -10, 10, 10))
    
    def roundPosition(self, value):
        value = value * self._scale
        value = round(value) - .5
        value = value * self._inverseScale
        return value
    
    def setGlyph(self, font, glyph):
        self._font = font
        self._glyph = glyph
        self._inverseScale = 0.1
        self._scale = 10
        self._showOffCurvePoints = True
        self._showOnCurvePoints = True
        
        self.translate(0, self.height()*(1+self._font.info.descender/self._font.info.unitsPerEm))
        self.scale(1, -1)
        self.addOutlines()
        self.addPoints()
        #self.openPath(glyph.getRepresentation("defconQt.QPainterPath"))

    def setRenderer(self, renderer):
        self.renderer = renderer

        if self.renderer == SvgView.OpenGL:
            if QGLFormat.hasOpenGL():
                self.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
        else:
            self.setViewport(QWidget())

    def setHighQualityAntialiasing(self, highQualityAntialiasing):
        if QGLFormat.hasOpenGL():
            self.setRenderHint(QPainter.HighQualityAntialiasing,
                    highQualityAntialiasing)

    def setViewBackground(self, enable):
        if self.backgroundItem:
            self.backgroundItem.setVisible(enable)

    def setViewOutline(self, enable):
        if self.outlineItem:
            self.outlineItem.setVisible(enable)

    def paintEvent(self, event):
        if self.renderer == SvgView.Image:
            if self.image.size() != self.viewport().size():
                self.image = QImage(self.viewport().size(),
                        QImage.Format_ARGB32_Premultiplied)

            imagePainter = QPainter(self.image)
            QGraphicsView.render(self, imagePainter)
            imagePainter.end()

            p = QPainter(self.viewport())
            p.drawImage(0, 0, self.image)
        else:
            super(SvgView, self).paintEvent(event)
            #self.drawOutlines()
            #self.drawPoints()

    def wheelEvent(self, event):
        factor = pow(1.2, event.angleDelta().y() / 120.0)
        self.scale(factor, factor)
        event.accept()


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    window = MainGfxWindow()
    if len(sys.argv) == 2:
        window.openFile(sys.argv[1])
    else:
        window.openFile(':/files/bubbles.svg')
    window.show()
    sys.exit(app.exec_())
