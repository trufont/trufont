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

        self.view = SvgView()
        self.view.setGlyph(font, glyph)

        fileMenu = QMenu("&File", self)
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

        rendererGroup = QActionGroup(self)
        rendererGroup.addAction(self.nativeAction)

        if QGLFormat.hasOpenGL():
            rendererGroup.addAction(self.glAction)

        rendererGroup.addAction(self.imageAction)

        self.menuBar().addMenu(rendererMenu)

        quitAction.triggered.connect(self.close)
        rendererGroup.triggered.connect(self.setRenderer)

        self.setCentralWidget(self.view)
        self.setWindowTitle("Glyph view")

    def setRenderer(self, action):
        if action == self.nativeAction:
            self.view.setRenderer(SvgView.Native)
        elif action == self.glAction:
            if QGLFormat.hasOpenGL():
                self.view.setRenderer(SvgView.OpenGL)
        elif action == self.imageAction:
            self.view.setRenderer(SvgView.Image)


class SvgView(QGraphicsView):
    Native, OpenGL, Image = range(3)

    def __init__(self, parent=None):
        super(SvgView, self).__init__(parent)

        self.renderer = SvgView.Native
        self._font = None
        self._glyph = None
        self._impliedPointSize = 1000
        self._pointSize = None
        
        self._inverseScale = 0.1
        self._scale = 10
        self._noPointSizePadding = 200
        self._bluesColor = QColor.fromRgbF(.5, .7, 1, .3)
        self._drawStroke = True
        self._showOffCurvePoints = True
        self._showOnCurvePoints = True
        self._bezierHandleColor = QColor.fromRgbF(1, 1, 1, .2)
        self._startPointColor = QColor.fromRgbF(1, 1, 1, .2)#Qt.blue
        self._backgroundColor = Qt.white#Qt.green
        self._offCurvePointColor = QColor.fromRgbF(.6, .6, .6, 1)#Qt.black
        self._onCurvePointColor = self._offCurvePointColor#Qt.red
        self._pointStrokeColor = QColor.fromRgbF(1, 1, 1, 1)#Qt.darkGray
        self._fillColor = QColor.fromRgbF(0, 0, 0, .4)#Qt.gray
        self._componentFillColor = QColor.fromRgbF(.2, .2, .3, .4)#Qt.darkGray

        self.setScene(QGraphicsScene(self))
        # XXX: this should allow us to move the view but doesn't happen...
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        # TODO: only set this for moving tool, also set bounding box...
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        # This rewinds view when scrolling, needed for check-board background
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

    def _getGlyphWidthHeight(self):
        if self._glyph.bounds:
            left, bottom, right, top = self._glyph.bounds
        else:
            left = right = bottom = top = 0
        left = min((0, left))
        right = max((right, self._glyph.width))
        bottom = self._font.info.descender
        top = max((self._font.info.capHeight, self._font.info.ascender, self._font.info.unitsPerEm + self._font.info.descender))
        width = abs(left) + right
        height = -bottom + top
        return width, height

    def _calcScale(self):
        if self.parent() is None:
            return
        if self._pointSize is None:
            visibleHeight = self.parent().height()
            fitHeight = visibleHeight
            glyphWidth, glyphHeight = self._getGlyphWidthHeight()
            glyphHeight += self._noPointSizePadding * 2
            self._scale = fitHeight / glyphHeight
        else:
            self._scale = self._pointSize / float(self._font.info.unitsPerEm)
        if self._scale <= 0:
            self._scale = .01
        self._inverseScale = 1.0 / self._scale
        self._impliedPointSize = self._font.info.unitsPerEm * self._scale

    def drawBackground(self, painter):
        painter.fillRect(self.viewport().rect(), self._backgroundColor)
        '''
        p.save()
        p.resetTransform()
        p.drawTiledPixmap(self.viewport().rect(),
                self.backgroundBrush().texture())
        p.restore()
        '''
    
    def drawBlues(self, painter):
        width = self.viewport().width()# * self._inverseScale
        font = self._glyph.getParent()
        #painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        if font is None:
            return
        attrs = ["postscriptBlueValues", "postscriptOtherBlues"]
        for attr in attrs:
            values = getattr(font.info, attr)
            if not values:
                continue
            yMins = [i for index, i in enumerate(values) if not index % 2]
            yMaxs = [i for index, i in enumerate(values) if index % 2]
            for yMin, yMax in zip(yMins, yMaxs):
                painter.fillRect(0, yMin, width, yMax - yMin, QBrush(self._bluesColor))
        
    def drawOutlines(self, painter):
        painter.save()
        # outlines
        path = self._glyph.getRepresentation("defconQt.NoComponentsQPainterPath")
        painter.setBrush(QBrush(self._fillColor))
        painter.drawPath(path)
        # components
        path = self._glyph.getRepresentation("defconQt.OnlyComponentsQPainterPath")
        painter.setBrush(QBrush(self._componentFillColor))
        painter.drawPath(path)
        painter.restore()

    def drawPoints(self, painter):
        # work out appropriate sizes and
        # skip if the glyph is too small
        pointSize = self._impliedPointSize
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
                    path.closeSubpath()
                else:
                    path.addEllipse(x-startHalf, y-startHalf, startWidth, startHeight)
            painter.save()
            painter.setBrush(QBrush(self._startPointColor))
            painter.drawPath(path)
            painter.restore()
        # off curve
        if self._showOffCurvePoints and outlineData["offCurvePoints"]:
            # lines
            path = QPainterPath()
            for point1, point2 in outlineData["bezierHandles"]:
                path.moveTo(*point1)
                path.lineTo(*point2)
            painter.save()
            painter.setPen(QPen(self._bezierHandleColor, 1.0))
            painter.drawPath(path)
            painter.restore()
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
            if self._drawStroke:
                painter.save()
                painter.setPen(QPen(self._pointStrokeColor, 3.0))
                painter.drawPath(path)
                painter.restore()
            painter.save()
            painter.setBrush(QBrush(self._backgroundColor))
            painter.drawPath(path)
            painter.restore()
            painter.save()
            painter.setPen(QPen(self._offCurvePointColor, 1.0))
            painter.drawPath(path)
            painter.restore()
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
            if self._drawStroke:
                painter.save()
                painter.setPen(QPen(self._pointStrokeColor, 3.0))
                painter.drawPath(path)
                painter.restore()
            painter.save()
            painter.setBrush(QBrush(self._onCurvePointColor))
            painter.drawPath(path)
            painter.restore()
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
    
    def roundPosition(self, value):
        value = value * self._scale
        value = round(value) - .5
        value = value * self._inverseScale
        return value
    
    def setGlyph(self, font, glyph):
        self._font = font
        self._glyph = glyph
        #self.scene().setSceneRect(*self._glyph.bounds)
        self.scene().setSceneRect(0, self._font.info.ascender, self._glyph.width, self._font.info.unitsPerEm)

    def setRenderer(self, renderer):
        self.renderer = renderer

        if self.renderer == SvgView.OpenGL:
            if QGLFormat.hasOpenGL():
                self.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
        else:
            self.setViewport(QWidget())

    def setViewBackground(self, enable):
        if self.backgroundItem:
            self.backgroundItem.setVisible(enable)

    def setViewOutline(self, enable):
        if self.outlineItem:
            self.outlineItem.setVisible(enable)

    def paintEvent(self, event):
        scene = self.scene()
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(0, self.height()*(1+self._font.info.descender/self._font.info.unitsPerEm))
        painter.scale(1, -1)
        self.drawBackground(painter)
        self.drawBlues(painter)
        self.drawOutlines(painter)
        self.drawPoints(painter)
    
        '''
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
        '''

    def wheelEvent(self, event):
        factor = pow(1.2, event.angleDelta().y() / 120.0)
        
        #self.setTransformationAnchor(QGraphicsView.NoAnchor)
        #self.setResizeAnchor(QGraphicsView.NoAnchor)
        #oldPos = self.mapToScene(event.pos())
        #self._calcScale()
        #self._setFrame()
        #self.scale(factor, factor)
        #newPos = self.mapToScene(event.pos())
        #delta = newPos - oldPos
        #self.translate(delta.x(), delta.y())
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
