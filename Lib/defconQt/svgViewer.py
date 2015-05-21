import math
from PyQt5.QtCore import QFile, QLineF, QObject, QPointF, QRectF, QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPixmap, QPen
from PyQt5.QtWidgets import (QActionGroup, QApplication, QFileDialog,
        QGraphicsItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
        QMainWindow, QMenu, QMessageBox, QStyle, QStyleOptionGraphicsItem, QWidget)
from PyQt5.QtOpenGL import QGL, QGLFormat, QGLWidget
from PyQt5.QtSvg import QGraphicsSvgItem


class MainGfxWindow(QMainWindow):
    def __init__(self, font=None, glyph=None, parent=None):
        super(MainGfxWindow, self).__init__(parent)

        self.view = GlyphView(font, glyph, self)

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
            self.view.setRenderer(GlyphView.Native)
        elif action == self.glAction:
            if QGLFormat.hasOpenGL():
                self.view.setRenderer(GlyphView.OpenGL)
        elif action == self.imageAction:
            self.view.setRenderer(GlyphView.Image)

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
        if (option.state & QStyle.State_Selected):
            pen = self.pen()
            pen.setColor(Qt.red)
            #pen.setWidth
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
        
    """
    def mouseMoveEvent(self, event):
        super(OnCurveSmoothPointItem, self).mouseMoveEvent(event)
        path = self.scene()._outlineItem.path()
        newX = self._pointX+self.pos().x()
        newY = self._pointY+self.pos().y()
        path.setElementPositionAt(self._pointIndex, newX, newY)
        if self._otherPointIndex is not None:
            path.setElementPositionAt(self._otherPointIndex, newX, newY)
            # TODO: the angle ought to be recalculated
            # maybe make it disappear on move and recalc when releasing
            # what does rf do here?
            if self._startPointObject is not None: self._startPointObject.setPos(self.pos())
        if self._prevCP is not None: self._prevCP.setPos(self.pos())
        if self._nextCP is not None: self._nextCP.setPos(self.pos())
        self.scene()._outlineItem.setPath(path)
        #self.scene().update()
    """
    
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
            index += len(prevContour)+1 # +1 for the moveTo to next contour
        if len(children) > 2:
            elemIndex = (self._pointIndex+selected-1) % len(self._contour)
        else:
            if path.elementAt((self._pointIndex-2) % len(self._contour)).isCurveTo():
                elemIndex = (self._pointIndex-1) % len(self._contour)
            else:
                elemIndex = (self._pointIndex+1) % len(self._contour)
        path.setElementPositionAt(index+elemIndex, self.pos().x()+newValue.x(), self.pos().y()+newValue.y())
        if not self._isSmooth or propagate is None: self.scene()._outlineItem.setPath(path); return
        targetLen = children[selected+1].line().length()+children[propagate+1].line().length()
        tmpLine = QLineF(newValue, QPointF(0, 0))
        tmpLine.setLength(targetLen)
        children[propagate].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        children[propagate].setPos(tmpLine.x2(), tmpLine.y2())
        children[propagate].setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        children[propagate+1].setLine(line.x1(), line.y1(), tmpLine.x2(), tmpLine.y2())
        path.setElementPositionAt(index+(self._pointIndex+propagate-1)%len(self._contour), self.pos().x()+tmpLine.x2(), self.pos().y()+tmpLine.y2())
        self.scene()._outlineItem.setPath(path)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene() is None: return QGraphicsItem.itemChange(self, change, value)
            #self._contour[self._pointIndex]
            path = self.scene()._outlineItem.path()
            """
            for i in range(path.elementCount()):
                elem = path.elementAt(i)
                if elem.isCurveTo(): kind = "curve"
                elif elem.isLineTo(): kind = "line"
                else: kind = "move"
                print("{}: {} {}".format(kind, elem.x, elem.y))
            print()
            """
            # TODO: if we're snapped to int round self.pos to int
            glyph = self.scene()._glyphObject
            index = 0
            cIndex = glyph.contourIndex(self._contour)
            for prevContour in glyph[:cIndex]:
                index += len(prevContour)+1 # +1 for the moveTo to next contour
            path.setElementPositionAt(index+self._pointIndex, self.pos().x(), self.pos().y())
            if self._pointIndex == 0:
                path.setElementPositionAt(index+len(self._contour), self.pos().x(), self.pos().y())
                # TODO: the angle ought to be recalculated
                # maybe make it disappear on move and recalc when releasing
                # what does rf do here?
                #if self._startPointObject is not None: self._startPointObject.setPos(self.pos())

            if len(self.childItems()) < 1: self.scene()._outlineItem.setPath(path); return QGraphicsItem.itemChange(self, change, value)
            elif len(self.childItems()) > 2:
                prevPos = self.childItems()[0].pos()
                path.setElementPositionAt(index + (self._pointIndex-1) % len(self._contour), self.pos().x()+prevPos.x(), self.pos().y()+prevPos.y())
                nextPos = self.childItems()[2].pos()
                path.setElementPositionAt(index + (self._pointIndex+1) % len(self._contour), self.pos().x()+nextPos.x(), self.pos().y()+nextPos.y())
            else:
                pos = self.childItems()[0].pos()
                ptIndex = 0
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
                if path.elementAt(index+(self._pointIndex-2) % len(self._contour)).isCurveTo():
                    ptIndex = self._pointIndex-1
                else:
                    ptIndex = self._pointIndex+1
                path.setElementPositionAt(index + (ptIndex) % len(self._contour), self.pos().x()+pos.x(), self.pos().y()+pos.y())
            self.scene()._outlineItem.setPath(path)
        return QGraphicsItem.itemChange(self, change, value)
    
    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        super(OnCurvePointItem, self).paint(painter, newOption, widget)
        if (option.state & QStyle.State_Selected):
            pen = self.pen()
            pen.setColor(Qt.red)
            self.setPen(pen)
        else:
            self.setPen(self._pen)

class GlyphScene(QGraphicsScene):
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left:
            x,y = -1,0
        elif key == Qt.Key_Up:
            x,y = 0,1
        elif key == Qt.Key_Right:
            x,y = 1,0
        elif key == Qt.Key_Down:
            x,y = 0,-1
        else:
            super(GlyphScene, self).keyPressEvent(event)
            return
        if len(self.selectedItems()) == 0:
            super(GlyphScene, self).keyPressEvent(event)
            return
        for item in self.selectedItems():
            # TODO: isinstance might be slow to use here, we might want to make a selectedMoveBy
            # function in items that calls moveBy for onCurve, noops for offCurve
            if isinstance(item, OffCurvePointItem) and item.parentItem().isSelected(): continue
            item.moveBy(x,y)
        event.accept()

class GlyphView(QGraphicsView):
    Native, OpenGL, Image = range(3)

    def __init__(self, font, glyph, parent=None):
        super(GlyphView, self).__init__(parent)

        self.renderer = GlyphView.Native
        self._font = font
        self._glyph = glyph
        self._impliedPointSize = 1000
        self._pointSize = None
        
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
        # off curve
        from collections import defaultdict
        offCurveIndex = defaultdict(lambda: defaultdict(dict))
        if self._showOffCurvePoints and outlineData["offCurvePoints"]:
            # lines
            for point1, point2, index, onCurveParentIndex in outlineData["bezierHandles"]:
                path = QPainterPath()
                path.moveTo(*point1)
                path.lineTo(*point2)
                prevOrNext = index < onCurveParentIndex
                offCurveIndex[onCurveParentIndex][prevOrNext]["bez"] = s.addPath(path, QPen(self._bezierHandleColor, 1.0))
            # points
            offWidth = offHeight = self.roundPosition(offCurvePointSize)# * self._inverseScale)
            offHalf = offWidth / 2.0
            #path = QPainterPath()
            for point, index, onCurveParentIndex in outlineData["offCurvePoints"]:
                x, y = point["point"]
                points.append((x, y))
                x = self.roundPosition(x - offHalf)
                y = self.roundPosition(y - offHalf)
                prevOrNext = index < onCurveParentIndex
                offCurveIndex[onCurveParentIndex][prevOrNext]["off"] = s.addEllipse(x, y, offWidth, offHeight,
                    QPen(self._offCurvePointColor, 1.0), QBrush(self._backgroundColor))
                item.setFlag(QGraphicsItem.ItemIsMovable)
            #if self._drawStroke:
            #    s.addPath(path, QPen(self._pointStrokeColor, 3.0))
            #s.addPath(path, QPen(Qt.NoPen), brush=)
            #s.addPath(path, )
        # on curve
        if self._showOnCurvePoints and outlineData["onCurvePoints"]:
            width = height = self.roundPosition(onCurvePointSize)# * self._inverseScale)
            half = width / 2.0
            smoothWidth = smoothHeight = self.roundPosition(onCurveSmoothPointSize)# * self._inverseScale)
            smoothHalf = smoothWidth / 2.0
            #path = QPainterPath()
            for point, index, isFirst in outlineData["onCurvePoints"]:
                x, y = point["point"]
                points.append((x, y))
                if point["smooth"]:
                    x = self.roundPosition(x - smoothHalf)
                    y = self.roundPosition(y - smoothHalf)
                    item = s.addEllipse(x, y, smoothWidth, smoothHeight,
                        QPen(self._pointStrokeColor, 1.5), QBrush(self._onCurvePointColor))
                    item.setFlag(QGraphicsItem.ItemIsMovable)
                    item.setFlag(QGraphicsItem.ItemIsSelectable)
                else:
                    rx = self.roundPosition(x - half)
                    ry = self.roundPosition(y - half)

                    lastPointInSubpath = None
                    startObject = None
                    if isFirst:
                        for lastPointIndex in outlineData["lastSubpathPoints"]:
                            if lastPointIndex > index:
                                lastPointInSubpath = lastPointIndex
                                break
                        startObject = startObjects.pop(0)

                    try: prevBez = offCurveIndex[index][True]["bez"]
                    except KeyError: prevBez = None
                    try: prevCP = offCurveIndex[index][True]["off"]
                    except KeyError: prevCP = None
                    try: nextBez = offCurveIndex[index][False]["bez"]
                    except KeyError: nextBez = None
                    try: nextCP = offCurveIndex[index][False]["off"]
                    except KeyError: nextCP = None
                    item = OnCurvePointItem(rx, ry, width, height, x, y, index, lastPointInSubpath,
                        startObject, prevBez, prevCP, nextBez, nextCP,
                        QPen(self._pointStrokeColor, 1.5), QBrush(self._onCurvePointColor))
                    s.addItem(item)
                    #item = s.addRect(x, y, width, height,
                    #    QPen(self._pointStrokeColor, 1.5), QBrush(self._onCurvePointColor))
                    #item.setFlag(QGraphicsItem.ItemIsMovable)
                    #item.setFlag(QGraphicsItem.ItemIsSelectable)
            #if self._drawStroke:
            #    s.addPath(path, )
            #myRect = s.addPath(path, QPen(Qt.NoPen), brush=)
            #myRect.setFlag(QGraphicsItem.ItemIsSelectable)
            #myRect.setFlag(QGraphicsItem.ItemIsMovable
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
        
        #self.setTransformationAnchor(QGraphicsView.NoAnchor)
        #self.setResizeAnchor(QGraphicsView.NoAnchor)
        #oldPos = self.mapToScene(event.pos())
        #self._calcScale()
        #self._setFrame()
        self.scale(factor, factor)
        self._calcScale()
        self.update()
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
