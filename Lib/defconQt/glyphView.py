import math
from PyQt5.QtCore import QFile, QLineF, QObject, QPointF, QRectF, QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QImage, QKeySequence, QPainter, QPainterPath, QPixmap, QPen
from PyQt5.QtWidgets import (QAction, QActionGroup, QApplication, QFileDialog,
        QGraphicsItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
        QMainWindow, QMenu, QMessageBox, QStyle, QStyleOptionGraphicsItem, QWidget)
from PyQt5.QtOpenGL import QGL, QGLFormat, QGLWidget
from PyQt5.QtSvg import QGraphicsSvgItem


class MainGfxWindow(QMainWindow):
    def __init__(self, font=None, glyph=None, parent=None):
        super(MainGfxWindow, self).__init__(parent)
        self.setAttribute(Qt.WA_KeyCompression)

        self.view = GlyphView(font, glyph, self)

        fileMenu = QMenu("&File", self)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)

        self.menuBar().addMenu(fileMenu)
        
        toolsMenu = QMenu("&Tools", self)
        
        self.selectTool = QAction("&Selection", toolsMenu)
        self.selectTool.setCheckable(True)
        self.selectTool.toggled.connect(self.view.setSceneSelection)
        toolsMenu.addAction(self.selectTool)

        self.drawingTool = QAction("&Drawing", toolsMenu)#toolsMenu.addAction("&Drawing")
        self.drawingTool.setCheckable(True)
        self.drawingTool.toggled.connect(self.view.setSceneDrawing)
        toolsMenu.addAction(self.drawingTool)
        
        self.toolsGroup = QActionGroup(self)#toolsMenu.addAction("&Selection")
        self.toolsGroup.addAction(self.selectTool)
        self.toolsGroup.addAction(self.drawingTool)
        self.selectTool.setChecked(True)
        
        #self.toolsGroup.toggled.connect(self.view.setSceneSelection)

        self.menuBar().addMenu(toolsMenu)

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

        rendererGroup.triggered.connect(self.setRenderer)

        self.setCentralWidget(self.view)
        self.setWindowTitle(glyph.name, font)
    
    def close(self):
        self.view._glyph.removeObserver(self, "Glyph.Changed")
        super(GlyphView, self).close()
    
    def _glyphChanged(self, event):
        self.view._glyphChanged(event)

    def setRenderer(self, action):
        if action == self.nativeAction:
            self.view.setRenderer(GlyphView.Native)
        elif action == self.glAction:
            if QGLFormat.hasOpenGL():
                self.view.setRenderer(GlyphView.OpenGL)
        elif action == self.imageAction:
            self.view.setRenderer(GlyphView.Image)

    def setWindowTitle(self, title, font=None):
        if font is not None: puts = "%s%s%s%s%s" % (title, " – ", font.info.familyName, " ", font.info.styleName)
        else: puts = title
        super(MainGfxWindow, self).setWindowTitle(puts)

class OffCurvePointItem(QGraphicsEllipseItem):
    def __init__(self, x, y, width, height, pointX, pointY, pen=None, brush=None, parent=None):
        super(OffCurvePointItem, self).__init__(x, y, width, height, parent)
        # since we have a parent, setPos must be relative to it
        self.setPos(pointX, pointY) # TODO: abstract and use pointX-self.parent().pos().x()
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        # TODO: stop doing this and go back to mouse events –> won't permit multiple selection
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        if pen is not None: self._pen = pen; self.setPen(pen)
        if brush is not None: self.setBrush(brush)
        
        self._pointX = pointX
        self._pointY = pointY
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.parentItem()._CPMoved(value)
        return QGraphicsItem.itemChange(self, change, value)
        
    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        super(OffCurvePointItem, self).paint(painter, newOption, widget)
        if option.state & QStyle.State_Selected:
            pen = self.pen()
            pen.setColor(Qt.red)
            self.setPen(pen)
        else:
            self.setPen(self._pen)

class OnCurvePointItem(QGraphicsPathItem):
    def __init__(self, x, y, width, height, pointX, pointY, isSmooth, contour, pointIndex,
            pen=None, brush=None, parent=None):
        path = QPainterPath()
        if isSmooth: path.addEllipse(x, y, width, height)
        else: path.addRect(x, y, width, height)
        super(OnCurvePointItem, self).__init__(path, parent)
        self.setPos(pointX, pointY)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        if pen is not None: self._pen = pen; self.setPen(pen)
        if brush is not None: self.setBrush(brush)

        self._contour = contour
        self._pointIndex = pointIndex
        self._isSmooth = isSmooth
    
    def _CPMoved(self, newValue):
        selected, propagate = None, None
        children = self.childItems()
        # nodes are at even positions
        for index, child in enumerate(children[::2]): # TODO: filter instead?
            if child.isSelected(): # eventually use isUnderMouse() if we implement multiple point selection
                selected = index * 2
            else:
                propagate = index * 2
        if selected is None: print("ARG"); return
        path = self.scene()._outlineItem.path()
        curValue = children[selected].pos()
        line = children[selected+1].line()
        children[selected+1].setLine(line.x1(), line.y1(), newValue.x(), newValue.y())

        glyph = self.scene()._glyphObject
        index = 0
        cIndex = glyph.contourIndex(self._contour)
        for prevContour in glyph[:cIndex]:
            index += len(prevContour) # +1 for the moveTo to next contour
            if not prevContour.open: index += 1
        if len(children) > 2:
            elemIndex = self._pointIndex+selected-1
        else:
            if path.elementAt((self._pointIndex-2) % len(self._contour)).isCurveTo():
                elemIndex = self._pointIndex-1
            else:
                elemIndex = self._pointIndex+1
        path.setElementPositionAt(index+elemIndex % len(self._contour), self.pos().x()+newValue.x(), self.pos().y()+newValue.y())
        self._contour[elemIndex].x = self.pos().x()+newValue.x()
        self._contour[elemIndex].y = self.pos().y()+newValue.y()
        self._contour.dirty = True
        if not self._isSmooth or propagate is None: self.scene()._outlineItem.setPath(path); return
        targetLen = children[selected+1].line().length()+children[propagate+1].line().length()
        tmpLine = QLineF(newValue, QPointF(0, 0))
        tmpLine.setLength(targetLen)
        children[propagate].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        children[propagate].setPos(tmpLine.x2(), tmpLine.y2())
        children[propagate].setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        children[propagate+1].setLine(line.x1(), line.y1(), tmpLine.x2(), tmpLine.y2())
        propagateInContour = self._pointIndex+propagate-1
        path.setElementPositionAt(index + (propagateInContour) % len(self._contour), self.pos().x()+tmpLine.x2(), self.pos().y()+tmpLine.y2())
        self._contour[propagateInContour].x = self.pos().x()+tmpLine.x2()
        self._contour[propagateInContour].y = self.pos().y()+tmpLine.y2()
        self.scene()._outlineItem.setPath(path)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene() is None: return QGraphicsItem.itemChange(self, change, value)
            # TODO: if we're snapped to int round self.pos to int
            # have a look at defcon FuzzyNumber as well
            self._contour[self._pointIndex].x = self.pos().x()
            self._contour[self._pointIndex].y = self.pos().y()
            self._contour.dirty = True
            path = self.scene()._outlineItem.path()
            glyph = self.scene()._glyphObject
            index = 0
            cIndex = glyph.contourIndex(self._contour)
            for prevContour in glyph[:cIndex]:
                index += len(prevContour) # +1 for the moveTo to next contour
                if not prevContour.open: index += 1
            path.setElementPositionAt(index+self._pointIndex, self.pos().x(), self.pos().y())
            if self._pointIndex == 0 and len(self._contour) > 1:
                path.setElementPositionAt(index+self._pointIndex+len(self._contour), self.pos().x(), self.pos().y())
                # TODO: the angle ought to be recalculated
                # maybe make it disappear on move and recalc when releasing
                # what does rf do here?
                #if self._startPointObject is not None: self._startPointObject.setPos(self.pos())
            '''
            for i in range(path.elementCount()):
                elem = path.elementAt(i)
                if elem.isCurveTo(): kind = "curve"
                elif elem.isLineTo(): kind = "line"
                else: kind = "move"
                print("{} {}: {} {}".format(i, kind, elem.x, elem.y))
            print()
            print(self._pointIndex)
            '''
            
            if len(self.childItems()) < 1: self.scene()._outlineItem.setPath(path); return QGraphicsItem.itemChange(self, change, value)
            elif len(self.childItems()) > 2:
                prevPos = self.childItems()[0].pos()
                path.setElementPositionAt(index + (self._pointIndex-1) % len(self._contour), self.pos().x()+prevPos.x(), self.pos().y()+prevPos.y())
                self._contour[self._pointIndex-1].x = self.pos().x()+prevPos.x()
                self._contour[self._pointIndex-1].y = self.pos().y()+prevPos.y()
                nextPos = self.childItems()[2].pos()
                path.setElementPositionAt(index + (self._pointIndex+1) % len(self._contour), self.pos().x()+nextPos.x(), self.pos().y()+nextPos.y())
                self._contour[self._pointIndex+1].x = self.pos().x()+nextPos.x()
                self._contour[self._pointIndex+1].y = self.pos().y()+nextPos.y()
            else:
                pos = self.childItems()[0].pos()
                ptIndex = 0
                if path.elementAt(index+(self._pointIndex-2) % len(self._contour)).isCurveTo():
                    ptIndex = self._pointIndex-1
                else:
                    ptIndex = self._pointIndex+1
                path.setElementPositionAt(index + (ptIndex) % len(self._contour), self.pos().x()+pos.x(), self.pos().y()+pos.y())
                self._contour[ptIndex].x = self.pos().x()+pos.x()
                self._contour[ptIndex].y = self.pos().y()+pos.y()
            self.scene()._outlineItem.setPath(path)
        return QGraphicsItem.itemChange(self, change, value)
    
    def mouseDoubleClickEvent(self, event):
        # TODO: stream
        x, y, width, height = -3, -3, 6, 6
        self._isSmooth = not self._isSmooth
        self._contour[self._pointIndex].smooth = self._isSmooth
        path = QPainterPath()
        if self._isSmooth: path.addEllipse(x, y, width, height)
        else: path.addRect(x, y, width, height)
        self.setPath(path)
    
    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        super(OnCurvePointItem, self).paint(painter, newOption, widget)
        if option.state & QStyle.State_Selected:
            pen = self.pen()
            pen.setColor(Qt.red)
            self.setPen(pen)
        else:
            self.setPen(self._pen)

class GlyphScene(QGraphicsScene):
    # TODO: implement key multiplex in a set()
    # http://stackoverflow.com/a/10568233/2037879
    def keyPressEvent(self, event):
        key = event.key()
        count = event.count()
        if key == Qt.Key_Left:
            x,y = -count,0
        elif key == Qt.Key_Up:
            x,y = 0,count
        elif key == Qt.Key_Right:
            x,y = count,0
        elif key == Qt.Key_Down:
            x,y = 0,-count
        else:
            super(GlyphScene, self).keyPressEvent(event)
            return
        if len(self.selectedItems()) == 0:
            super(GlyphScene, self).keyPressEvent(event)
            return
        for item in self.selectedItems():
            # TODO: isinstance might be slow to use here, we might want to make a selectedMoveBy
            # function in items that calls moveBy for onCurve, noops for offCurve
            if isinstance(item, OffCurvePointItem) and item.parentItem().isSelected(): print("yea"); continue
            item.moveBy(x,y)
        event.accept()
    
    def mousePressEvent(self, event):
        # TODO: store this in scene
        if not self.views()[0]._drawingTool: super(GlyphScene, self).mousePressEvent(event); return
        # TODO: stream
        half, width, height = 3, 6, 6
        touched = self.itemAt(event.scenePos(), self.views()[0].transform())
        sel = self.selectedItems()
        x, y = event.scenePos().x(), event.scenePos().y()
        # XXX: not sure why isinstance does not work here
        # contour.open is there in case we tackle extension from first point.
        # what does rf do here?
        if len(sel) == 1 and (type(sel[0]) is OnCurvePointItem) and sel[0]._contour.open \
              and (sel[0]._pointIndex == len(sel[0]._contour)-1):
            close = False
            path = self._outlineItem.path()
            pointIndex = len(sel[0]._contour)
            if (touched and isinstance(touched, OnCurvePointItem)) and touched._pointIndex == 0 \
                  and sel[0]._contour == touched._contour:
                close = True
                x, y = touched.pos().x(), touched.pos().y()
            elif touched and isinstance(touched, OnCurvePointItem):
                super(GlyphScene, self).mousePressEvent(event)
                return
            else:
                item = OnCurvePointItem(-half, -half, width, height, x, y, False, 
                            sel[0]._contour, pointIndex, QPen(Qt.black, 1.5), QBrush(Qt.white))#QPen(self._pointStrokeColor, 1.5), QBrush(self._onCurvePointColor))
                self.addItem(item)
            path.lineTo(x, y)
            if close: path.closeSubpath()
            self._outlineItem.setPath(path)
            if not close:
                sel[0]._contour.addPoint((x,y), "line")
                event.accept()
            else:
                # Changing the first point from move to line/curve will cycle and so close the contour
                sel[0]._contour[0].segmentType = "line"
        elif not (touched and isinstance(touched, OnCurvePointItem)):
            path = self._outlineItem.path()
            path.moveTo(x, y)
            self._outlineItem.setPath(path)

            from defcon.objects.contour import Contour
            nextC = Contour()
            self.views()[0]._glyph.appendContour(nextC)
            nextC.addPoint((x,y), "move")

            item = OnCurvePointItem(-half, -half, width, height, x, y, False, 
                        self.views()[0]._glyph[-1], 0, QPen(Qt.black, 1.5), QBrush(Qt.white))#QPen(self._pointStrokeColor, 1.5), QBrush(self._onCurvePointColor))
            self.addItem(item)
            event.accept()
        super(GlyphScene, self).mousePressEvent(event)

class GlyphView(QGraphicsView):
    Native, OpenGL, Image = range(3)

    def __init__(self, font, glyph, parent=None):
        super(GlyphView, self).__init__(parent)

        self.renderer = GlyphView.Native
        self._font = font
        self._glyph = glyph
        self._glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
        self._impliedPointSize = 1000
        self._pointSize = None
        
        self._drawingTool = False
        
        self._inverseScale = 0.1
        self._scale = 10
        self._noPointSizePadding = 200
        self._bluesColor = QColor.fromRgbF(.5, .7, 1, .3)
        self._drawStroke = True
        self._showOffCurvePoints = True
        self._showOnCurvePoints = True
        self._bezierHandleColor = QColor.fromRgbF(0, 0, 0, .2)
        self._startPointColor = QColor.fromRgbF(0, 0, 0, .2)#Qt.blue
        self._backgroundColor = Qt.white#Qt.green
        self._offCurvePointColor = QColor.fromRgbF(.6, .6, .6, 1)#Qt.black
        self._onCurvePointColor = self._offCurvePointColor#Qt.red
        self._pointStrokeColor = QColor.fromRgbF(1, 1, 1, 1)#Qt.darkGray
        self._fillColor = QColor.fromRgbF(0, 0, 0, .4)#Qt.gray
        self._componentFillColor = QColor.fromRgbF(.2, .2, .3, .4)#Qt.darkGray

        self.setScene(GlyphScene(self))
        #self.scene().setSceneRect(0, self._font.info.ascender, self._glyph.width, self._font.info.unitsPerEm)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        # This rewinds view when scrolling, needed for check-board background
        #self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.setRenderHint(QPainter.Antialiasing)
        self.translate(0, self.height()*(1+self._font.info.descender/self._font.info.unitsPerEm))
        self.scale(1, -1)
        self.addBackground()
        self.addBlues()
        self.addOutlines()
        self.addPoints()

        # Prepare background check-board pattern.
        """
        tilePixmap = QPixmap(64, 64)
        tilePixmap.fill(Qt.white)
        tilePainter = QPainter(tilePixmap)
        color = QColor(220, 220, 220)
        tilePainter.fillRect(0, 0, 32, 32, color)
        tilePainter.fillRect(32, 32, 32, 32, color)
        tilePainter.end()
        """

        #self.setBackgroundBrush(QBrush(tilePixmap))
    
    def _glyphChanged(self, event):
        pass
        '''
        self.scene().clear()
        self.addBackground()
        self.addBlues()
        self.addOutlines()
        self.addPoints()
        '''

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
        #if self.viewport() is None:
        #    return
        if self._pointSize is None:
            visibleHeight = self.viewport().height()
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
        
    def addBackground(self):
        s = self.scene()
        s.addRect(QRectF(self.viewport().rect()), QPen(Qt.NoPen), QBrush(self._backgroundColor))
    
    def addBlues(self):
        s = self.scene()
        width = self._glyph.width# * self._inverseScale
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
                s.addRect(0, yMin, width, yMax - yMin, QPen(Qt.NoPen), QBrush(self._bluesColor))
        
    def addOutlines(self):
        s = self.scene()
        # outlines
        path = self._glyph.getRepresentation("defconQt.NoComponentsQPainterPath")
        self.scene()._outlineItem = s.addPath(path, brush=QBrush(self._fillColor))
        self.scene()._glyphObject = self._glyph
        # components
        path = self._glyph.getRepresentation("defconQt.OnlyComponentsQPainterPath")
        s.addPath(path, brush=QBrush(self._componentFillColor))

    def addPoints(self):
        s = self.scene()
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
        points = [] # TODO: remove this unless we need it # useful for text drawing, add it
        startObjects = []
        offWidth = offHeight = self.roundPosition(offCurvePointSize)# * self._inverseScale)
        offHalf = offWidth / 2.0
        width = height = self.roundPosition(onCurvePointSize)# * self._inverseScale)
        half = width / 2.0
        smoothWidth = smoothHeight = self.roundPosition(onCurveSmoothPointSize)# * self._inverseScale)
        smoothHalf = smoothWidth / 2.0
        if outlineData["onCurvePoints"]:
            for onCurve in outlineData["onCurvePoints"]:
                # on curve
                x, y = onCurve.x, onCurve.y
                points.append((x, y))
                if onCurve.isSmooth:
                    rx = self.roundPosition(x - smoothHalf)
                    ry = self.roundPosition(y - smoothHalf)
                    item = OnCurvePointItem(-smoothHalf, -smoothHalf, smoothWidth, smoothHeight, x, y,
                        onCurve.isSmooth, self._glyph[onCurve.contourIndex], onCurve.pointIndex,
                        QPen(self._pointStrokeColor, 1.5), QBrush(self._onCurvePointColor))
                    s.addItem(item)
                else:
                    rx = self.roundPosition(x - half)
                    ry = self.roundPosition(y - half)
                    item = OnCurvePointItem(-half, -half, width, height, x, y, onCurve.isSmooth, 
                        self._glyph[onCurve.contourIndex], onCurve.pointIndex,
                        QPen(self._pointStrokeColor, 1.5), QBrush(self._onCurvePointColor))
                    s.addItem(item)
                # off curve
                for CP in [onCurve.prevCP, onCurve.nextCP]:
                    if CP:
                        cx, cy = CP
                        # point
                        points.append((cx, cy))
                        rx = self.roundPosition(cx - offHalf)
                        ry = self.roundPosition(cy - offHalf)
                        CPObject = OffCurvePointItem(-offHalf, -offHalf, offWidth, offHeight, cx-x, cy-y,
                            QPen(self._offCurvePointColor, 1.0), QBrush(self._backgroundColor), item)
                        # line
                        lineObj = QGraphicsLineItem(0, 0, cx - x, cy - y, item)
                        lineObj.setPen(QPen(self._bezierHandleColor, 1.0))
                    
        '''
        # start point
        if self._showOnCurvePoints and outlineData["startPoints"]:
            startWidth = startHeight = self.roundPosition(startPointSize)# * self._inverseScale)
            startHalf = startWidth / 2.0
            for point, angle in outlineData["startPoints"]:
                x, y = point
                # TODO: do we really need to special-case with Qt?
                if angle is not None:
                    path = QPainterPath()
                    path.moveTo(x, y)
                    path.arcTo(x-startHalf, y-startHalf, 2*startHalf, 2*startHalf, angle-90, -180)
                    item = s.addPath(path, QPen(Qt.NoPen), QBrush(self._startPointColor))
                    startObjects.append(item)
                    #path.closeSubpath()
                else:
                    item = s.addEllipse(x-startHalf, y-startHalf, startWidth, startHeight,
                        QPen(Qt.NoPen), QBrush(self._startPointColor))
                    startObjects.append(item)
            #s.addPath(path, QPen(Qt.NoPen), brush=QBrush(self._startPointColor))
        # text
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
        '''

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

        if self.renderer == GlyphView.OpenGL:
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
    
    def mousePressEvent(self, event):
        if (event.button() == Qt.MidButton):
            if self.dragMode() == QGraphicsView.RubberBandDrag:
                self.setDragMode(QGraphicsView.ScrollHandDrag)
            else:
                self.setDragMode(QGraphicsView.RubberBandDrag)
        super(GlyphView, self).mousePressEvent(event)
    
    def setSceneDrawing(self):
        #self.parent().drawingTool.setChecked(True)
        #self.parent().selectTool.setChecked(False)
        self._drawingTool = True
    
    def setSceneSelection(self):
        #self.parent().drawingTool.setChecked(False)
        #self.parent().selectTool.setChecked(True)
        self._drawingTool = False
    
    # Lock/release handdrag does not seem to work…
    '''
    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.MidButton):
            self.setDragMode(QGraphicsView.RubberBandDrag)
        super(GlyphView, self).mouseReleaseEvent(event)
    '''

    '''
    def paintEvent(self, event):
        if self.renderer == GlyphView.Image:
            if self.image.size() != self.viewport().size():
                self.image = QImage(self.viewport().size(),
                        QImage.Format_ARGB32_Premultiplied)

            imagePainter = QPainter(self.image)
            QGraphicsView.render(self, imagePainter)
            imagePainter.end()

            p = QPainter(self.viewport())
            p.drawImage(0, 0, self.image)
        else:
            super(GlyphView, self).paintEvent(event)
    '''

    def wheelEvent(self, event):
        factor = pow(1.2, event.angleDelta().y() / 120.0)

        #self._calcScale()
        #self._setFrame()
        self.scale(factor, factor)
        '''
        for item in self.scene().items():
            if isinstance(item, OnCurvePointItem):
                path = QPainterPath()
                onCurvePointSize = 10 / self.transform().m11()
                width = height = self.roundPosition(onCurvePointSize)# * self._inverseScale)
                half = width / 2.0
                path.addEllipse(-half, -half, width, height)
                item.setPath(path)
                #item.setTransform(self.transform().inverted()[0])
        '''
        self.update()
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
