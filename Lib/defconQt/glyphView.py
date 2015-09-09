from enum import Enum
from math import copysign
from PyQt5.QtCore import *#QFile, QLineF, QObject, QPointF, QRectF, QSize, Qt
from PyQt5.QtGui import *#QBrush, QColor, QImage, QKeySequence, QPainter, QPainterPath, QPixmap, QPen
from PyQt5.QtWidgets import *#(QAction, QActionGroup, QApplication, QFileDialog,
        #QGraphicsItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
        #QMainWindow, QMenu, QMessageBox, QStyle, QStyleOptionGraphicsItem, QWidget)
from PyQt5.QtOpenGL import QGL, QGLFormat, QGLWidget


class MainGfxWindow(QMainWindow):
    def __init__(self, font=None, glyph=None, parent=None):
        super(MainGfxWindow, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_KeyCompression)

        self.view = GlyphView(font, glyph, self)

        fileMenu = QMenu("&File", self)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)

        self.menuBar().addMenu(fileMenu)
        
        toolsMenu = QMenu("&Tools", self)
        
        self.selectTool = toolsMenu.addAction("&Selection")
        self.selectTool.setCheckable(True)
        self.selectTool.toggled.connect(self.view.setSceneSelection)

        self.drawingTool = toolsMenu.addAction("&Drawing")
        self.drawingTool.setCheckable(True)
        self.drawingTool.toggled.connect(self.view.setSceneDrawing)
        
        self.rulerTool = toolsMenu.addAction("&Ruler")
        self.rulerTool.setCheckable(True)
        self.rulerTool.toggled.connect(self.view.setSceneRuler)
        
        self.toolsGroup = QActionGroup(self)
        self.toolsGroup.addAction(self.selectTool)
        self.toolsGroup.addAction(self.drawingTool)
        self.toolsGroup.addAction(self.rulerTool)
        self.selectTool.setChecked(True)

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
        self.adjustSize()
    
    def close(self):
        self.view._glyph.removeObserver(self, "Glyph.Changed")
        super(GlyphView, self).close()
    
    def _glyphChanged(self, notification):
        self.view._glyphChanged(notification)

    def setRenderer(self, action):
        if action == self.nativeAction:
            self.view.setRenderer(GlyphView.Native)
        elif action == self.glAction:
            if QGLFormat.hasOpenGL():
                self.view.setRenderer(GlyphView.OpenGL)
        elif action == self.imageAction:
            self.view.setRenderer(GlyphView.Image)

    def setWindowTitle(self, title, font=None):
        if font is not None: title = "%s – %s %s" % (title, font.info.familyName, font.info.styleName)
        super(MainGfxWindow, self).setWindowTitle(title)

def roundPosition(value):
    value = value * 10#self._scale
    value = round(value) - .5
    value = value * .1#self._inverseScale
    return value

offCurvePointSize = 8#5
onCurvePointSize = 9#6
onCurveSmoothPointSize = 10#7
offWidth = offHeight = roundPosition(offCurvePointSize)# * self._inverseScale)
offHalf = offWidth / 2.0
onWidth = onHeight = roundPosition(onCurvePointSize)# * self._inverseScale)
onHalf = onWidth / 2.0
smoothWidth = smoothHeight = roundPosition(onCurveSmoothPointSize)# * self._inverseScale)
smoothHalf = smoothWidth / 2.0
onCurvePenWidth = 1.5
offCurvePenWidth = 1.0

bezierHandleColor = QColor.fromRgbF(0, 0, 0, .2)
startPointColor = QColor.fromRgbF(0, 0, 0, .2)
backgroundColor = Qt.white
offCurvePointColor = QColor.fromRgbF(.6, .6, .6, 1)
onCurvePointColor = offCurvePointColor
pointStrokeColor = QColor.fromRgbF(1, 1, 1, 1)
pointSelectionColor = Qt.red

class SceneTools(Enum):
    SelectionTool = 0
    DrawingTool = 1
    RulerTool = 2

class HandleLineItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, parent):
        super(HandleLineItem, self).__init__(x1, y1, x2, y2, parent)
        self.setPen(QPen(bezierHandleColor, 1.0))
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)

class OffCurvePointItem(QGraphicsEllipseItem):
    def __init__(self, x, y, parent=None):
        super(OffCurvePointItem, self).__init__(parent)
        # since we have a parent, setPos must be relative to it
        self.setPointPath()
        self.setPos(x, y) # TODO: abstract and use pointX-self.parent().pos().x()
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)

        self.setBrush(QBrush(backgroundColor))
        self._needsUngrab = False
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
            if QApplication.keyboardModifiers() & Qt.ShiftModifier \
                  and len(self.scene().selectedItems()) == 1:
                ax = abs(value.x())
                ay = abs(value.y())
                if ay >= ax * 2:
                    value.setX(0)
                elif ay > ax / 2:
                    avg = (ax + ay) / 2
                    value.setX(copysign(avg, value.x()))
                    value.setY(copysign(avg, value.y()))
                else:
                    value.setY(0)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.parentItem()._CPMoved(value)
        return value
    
    def mousePressEvent(self, event):
        if not self._needsUngrab and self.x() == 0 and self.y() == 0:
            event.ignore()
        super(OffCurvePointItem, self).mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        super(OffCurvePointItem, self).mouseReleaseEvent(event)
        if self._needsUngrab:
            self.ungrabMouse()
            self._needsUngrab = False
        
    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        #if self.x() == 0 and self.y() == 0: return
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        pen = self.pen()
        if option.state & QStyle.State_Selected:
            pen.setColor(pointSelectionColor)
        else:
            pen.setColor(offCurvePointColor)
        self.setPen(pen)
        super(OffCurvePointItem, self).paint(painter, newOption, widget)
    
    def setPointPath(self, scale=None):
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 4: scale = 4
        elif scale < .4: scale = .4
        self.prepareGeometryChange()
        self.setRect(-offHalf/scale, -offHalf/scale, offWidth/scale, offHeight/scale)
        self.setPen(QPen(offCurvePointColor, 1.0/scale))

class OnCurvePointItem(QGraphicsPathItem):
    def __init__(self, x, y, isSmooth, contour, point, scale=1, parent=None):
        super(OnCurvePointItem, self).__init__(parent)
        self._contour = contour
        self._point = point
        self._isSmooth = isSmooth
        self._posBeforeMove = None

        self.setPointPath(scale)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(onCurvePointColor))
    
    def delete(self, preserveShape=True):
        def findNextOnCurve(self, index=0):
            for _ in self._contour:
                if self._contour[index].segmentType is not None:
                    break
                index = (index+1) % len(self._contour)
            return index

        scene = self.scene()
        glyph = scene._glyphObject
        scene._blocked = True
        if len(self._contour.segments) < 2:
            glyph.removeContour(self._contour)
        else:
            ptIndex = self.getPointIndex()
            if self._contour.open and ptIndex == 0:
                nextOnCurveIndex = findNextOnCurve(self, 1)
                self._contour._points = self._contour[nextOnCurveIndex:]
                self._contour[0].segmentType = "move"
                self._contour.dirty = True
            else:
                # Using preserveShape at the edge of an open contour will traceback
                if ptIndex == len(self._contour): preserveShape = False
                self._contour.removeSegment(self.getSegmentIndex(), preserveShape)
                nextOnCurveIndex = findNextOnCurve(self)
                self._contour.setStartPoint(nextOnCurveIndex)
        scene._blocked = False
        scene.removeItem(self)
    
    def setPointPath(self, scale=None):
        path = QPainterPath()
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 4: scale = 4
        elif scale < .4: scale = .4
        if self._isSmooth:
            path.addEllipse(-smoothHalf/scale, -smoothHalf/scale, smoothWidth/scale, smoothHeight/scale)
        else:
            path.addRect(-onHalf/scale, -onHalf/scale, onWidth/scale, onHeight/scale)
        self.prepareGeometryChange()
        self.setPath(path)
        self.setPen(QPen(pointStrokeColor, 1.5/scale))
    
    def getPointIndex(self):
        return self._contour.index(self._point)
    
    def getSegmentIndex(self):
        # closed contour cycles and so the "previous" segment goes to current point
        index = 0 if self._contour.open else -1
        for pt in self._contour:
            if pt == self._point: break
            if pt.segmentType is not None: index += 1
        return index % len(self._contour.segments)
    
    def _CPMoved(self, newValue):
        pointIndex = self.getPointIndex()
        children = self.childItems()
        # nodes are stored after lines (for stacking order)
        if children[1].isSelected():
            selected = 1
            propagate = 3
        else:
            selected = 3
            propagate = 1
        curValue = children[selected].pos()
        line = children[selected-1].line()
        children[selected-1].setLine(line.x1(), line.y1(), newValue.x(), newValue.y())

        if not len(children) > 4:
            elemIndex = pointIndex-2+selected
            self._contour[elemIndex].x = self.pos().x()+newValue.x()
            self._contour[elemIndex].y = self.pos().y()+newValue.y()
        if not (self._isSmooth and children[propagate].isVisible()):
            self.setShallowDirty()
            return
        if children[selected]._needsUngrab:
            targetLen = children[selected-1].line().length()*2
        else:
            targetLen = children[selected-1].line().length()+children[propagate-1].line().length()
        tmpLine = QLineF(newValue, QPointF(0, 0))
        tmpLine.setLength(targetLen)
        children[propagate].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        children[propagate].setPos(tmpLine.x2(), tmpLine.y2())
        children[propagate].setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        children[propagate-1].setLine(line.x1(), line.y1(), tmpLine.x2(), tmpLine.y2())
        propagateInContour = pointIndex-2+propagate
        self._contour[propagateInContour].x = self.pos().x()+tmpLine.x2()
        self._contour[propagateInContour].y = self.pos().y()+tmpLine.y2()
        self.setShallowDirty()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # have a look at defcon FuzzyNumber as well
            pointIndex = self.getPointIndex()
            self._contour[pointIndex].x = self.pos().x()
            self._contour[pointIndex].y = self.pos().y()

            children = self.childItems()
            if children[1].isVisible():
                prevPos = children[1].pos()
                self._contour[pointIndex-1].x = self.pos().x()+prevPos.x()
                self._contour[pointIndex-1].y = self.pos().y()+prevPos.y()
            if children[3].isVisible():
                nextPos = children[3].pos()
                self._contour[pointIndex+1].x = self.pos().x()+nextPos.x()
                self._contour[pointIndex+1].y = self.pos().y()+nextPos.y()
            self.setShallowDirty()
        return value
    
    def setShallowDirty(self):
        scene = self.scene()
        scene._blocked = True
        self._contour.dirty = True
        scene._blocked = False
    
    def mouseMoveEvent(self, event):
        modifiers = event.modifiers()
        children = self.childItems()
        # Ctrl: get and move prevCP, Alt: nextCP
        if modifiers & Qt.ControlModifier and children[1].x() == 0 and children[1].y() == 0:
            i, o = 1, 3
        elif modifiers & Qt.AltModifier and children[3].x() == 0 and children[3].y() == 0:
            i, o = 3, 1
        elif not (modifiers & Qt.ControlModifier or modifiers & Qt.AltModifier):
            super(OnCurvePointItem, self).mouseMoveEvent(event)
            return
        else: # eat the event if we are not going to yield an offCP
            event.accept()
            return
        ptIndex = self.getPointIndex()
        scene = self.scene()
        scene._blocked = True
        # if we have line segment, insert offCurve points
        insertIndex = (ptIndex+(i-1)//2) % len(self._contour)
        if self._contour[insertIndex].segmentType == "line":
            nextToCP = self._contour[(ptIndex-2+i) % len(self._contour)]
            assert(nextToCP.segmentType is not None)
            self._contour[insertIndex].segmentType = "curve"
            if i == 1:
                first, second = (self._point.x, self._point.y), (nextToCP.x, nextToCP.y)
            else:
                first, second = (nextToCP.x, nextToCP.y), (self._point.x, self._point.y)
            self._contour.insertPoint(insertIndex, self._contour._pointClass(first))
            self._contour.insertPoint(insertIndex, self._contour._pointClass(second))
            children[i].setVisible(True)
            # TODO: need a list of items to make this efficient
            scene.getItemForPoint(nextToCP).childItems()[o].setVisible(True)
        # release current onCurve
        scene.sendEvent(self, QEvent(QEvent.MouseButtonRelease))
        scene.mouseGrabberItem().ungrabMouse()
        self.setSelected(False)
        self.setIsSmooth(False)
        children[i]._needsUngrab = True
        scene.sendEvent(children[i], QEvent(QEvent.MouseButtonPress))
        children[i].setSelected(True)
        children[i].grabMouse()
        scene._blocked = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        self.setIsSmooth(not self._isSmooth)
    
    def setIsSmooth(self, isSmooth):
        self._isSmooth = isSmooth
        self._point.smooth = self._isSmooth
        self.setShallowDirty()
        self.setPointPath()
    
    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        pen = self.pen()
        if option.state & QStyle.State_Selected:
            pen.setColor(pointSelectionColor)
        else:
            pen.setColor(pointStrokeColor)
        self.setPen(pen)
        super(OnCurvePointItem, self).paint(painter, newOption, widget)

class ResizeHandleItem(QGraphicsRectItem):
    def __init__(self, parent=None):
        super(QGraphicsRectItem, self).__init__(parent)
        self.setPointPath()
        self.setBrush(QBrush(QColor(60, 60, 60)))
        self.setPen(QPen(Qt.NoPen))
        self.setFlag(QGraphicsItem.ItemIgnoresParentOpacity)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        #self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setCursor(Qt.SizeFDiagCursor)
        
        rect = self.parentItem().boundingRect()
        self.setPos(rect.width(), rect.height())
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if not value: self.setVisible(value)
        return value
    
    def mouseMoveEvent(self, event):
        self.parentItem()._pixmapGeometryChanged(event)
    
    def setPointPath(self, scale=None):
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 4: scale = 4
        self.prepareGeometryChange()
        self.setRect(-onHalf/scale, -onHalf/scale, onWidth/scale, onHeight/scale)

class PixmapItem(QGraphicsPixmapItem):
    def __init__(self, x, y, pixmap, parent=None):
        super(QGraphicsPixmapItem, self).__init__(pixmap, parent)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setTransform(QTransform().fromScale(1, -1))
        self.setOpacity(.5)
        self.setZValue(-1)

        rect = self.boundingRect()
        self._rWidth = rect.width()
        self._rHeight = rect.height()
        handle = ResizeHandleItem(self)
        handle.setVisible(False)
    
    def _pixmapGeometryChanged(self, event):
        modifiers = event.modifiers()
        pos = event.scenePos()
        if modifiers & Qt.ControlModifier:
            # rotate
            refLine = QLineF(self.x(), self.y(), self.x()+self._rWidth, self.y()-self._rHeight)
            curLine = QLineF(self.x(), self.y(), pos.x(), pos.y())
            self.setRotation(refLine.angleTo(curLine))
        else:
            # scale
            dy = (pos.y() - self.y()) / self._rHeight
            if modifiers & Qt.ShiftModifier:
                # keep original aspect ratio
                dx = -dy
            else:
                dx = (pos.x() - self.x()) / self._rWidth
            self.setTransform(QTransform().fromScale(dx, dy))
        event.accept()
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            children = self.childItems()
            if not children[0].isUnderMouse():
                children[0].setVisible(value)
        return value

class GlyphScene(QGraphicsScene):
    def __init__(self, parent):
        super(GlyphScene, self).__init__(parent)
        self._editing = False
        self._integerPlane = True
        self._cachedRuler = None
        self._rulerObject = None
        self._dataForUndo = []
        self._dataForRedo = []

        font = self.font()
        font.setFamily("Roboto Mono")
        font.setFixedPitch(True)
        self.setFont(font)
        
        self._blocked = False
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(GlyphScene, self).dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(GlyphScene, self).dragMoveEvent(event)
    
    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            paths = mimeData.urls()
            # only support the drop of one image for now
            dragPix = QPixmap(paths[0].toLocalFile())
            event.setAccepted(not dragPix.isNull())
        else:
            return
        pos = event.scenePos()
        newPix = PixmapItem(pos.x(), pos.y(), dragPix)
        self.addItem(newPix)
        event.acceptProposedAction()
    
    def getItemForPoint(self, point):
        for item in self.items():
            if isinstance(item, OnCurvePointItem) and item._point == point:
                return item
        return None
    
    def getViewScale(self):
        return self.views()[0].transform().m11()

    # TODO: implement key multiplex in a set()
    # http://stackoverflow.com/a/10568233/2037879
    def keyPressEvent(self, event):
        key = event.key()
        count = event.count()
        modifiers = event.modifiers()
        # XXX: clean this up, prioritize key dispatching before processing things
        # TODO: this is not DRY w space center, put this in a function
        if modifiers & Qt.ShiftModifier:
            count *= 10
            if modifiers & Qt.ControlModifier:
                count *= 10
        if key == Qt.Key_Left:
            x,y = -count,0
        elif key == Qt.Key_Up:
            x,y = 0,count
        elif key == Qt.Key_Right:
            x,y = count,0
        elif key == Qt.Key_Down:
            x,y = 0,-count
        elif key == Qt.Key_Delete:
            for item in self.selectedItems():
                if isinstance(item, OnCurvePointItem):
                    item.delete(not event.modifiers() & Qt.ShiftModifier)
                elif isinstance(item, PixmapItem):
                    self.removeItem(item)
            event.accept()
            return
        elif event.matches(QKeySequence.Undo):
            if len(self._dataForUndo) > 0:
                undo = self._dataForUndo.pop()
                redo = self._glyphObject.getDataToSerializeForUndo()
                self._glyphObject.loadDeserializedDataFromUndo(undo)
                self._dataForRedo.append(redo)
            event.accept()
            return
        elif event.matches(QKeySequence.Redo):
            if len(self._dataForRedo) > 0:
                undo = self._glyphObject.getDataToSerializeForUndo()
                redo = self._dataForRedo.pop()
                self._dataForUndo.append(undo)
                self._glyphObject.loadDeserializedDataFromUndo(redo)
            event.accept()
            return
        elif event.matches(QKeySequence.SelectAll):
            path = QPainterPath()
            path.addRect(self.sceneRect())
            view = self.views()[0]
            self.setSelectionArea(path, view.transform())
            event.accept()
            return
        elif modifiers & Qt.ControlModifier and key == Qt.Key_D:
            view = self.views()[0]
            self.setSelectionArea(QPainterPath(), view.transform())
            event.accept()
            return
        else:
            sel = self.selectedItems()
            if len(sel) == 1 and isinstance(sel[0], OffCurvePointItem) and \
              sel[0].parentItem().getPointIndex() == len(sel[0].parentItem()._contour)-2 and \
              key == Qt.Key_Alt and self._editing is not False:
                sel[0].parentItem().setIsSmooth(False)
            super(GlyphScene, self).keyPressEvent(event)
            return
        if len(self.selectedItems()) == 0:
            super(GlyphScene, self).keyPressEvent(event)
            return
        for item in self.selectedItems():
            # TODO: if isinstance turns out to be slow, we might want to make a selectedMoveBy
            # function in items that calls moveBy for onCurve, noops for offCurve
            if isinstance(item, OffCurvePointItem) and item.parentItem().isSelected(): continue
            item.moveBy(x,y)
        event.accept()
    
    def keyReleaseEvent(self, event):
        sel = self.selectedItems()
        if len(sel) == 1 and isinstance(sel[0], OffCurvePointItem) and \
          sel[0].parentItem().getPointIndex() == len(sel[0].parentItem()._contour)-2 and \
          event.key() == Qt.Key_Alt and self._editing is not False:
            sel[0].parentItem().setIsSmooth(True)
        super(GlyphScene, self).keyReleaseEvent(event)

    def mousePressEvent(self, event):
        view = self.views()[0]
        touched = self.itemAt(event.scenePos(), view.transform())
        if view._currentTool == SceneTools.RulerTool:
            self.rulerMousePress(event)
            return
        else:
            data = self._glyphObject.getDataToSerializeForUndo()
            self._dataForUndo.append(data)
            self._dataForRedo = []
            if not view._currentTool == SceneTools.DrawingTool:
                super(GlyphScene, self).mousePressEvent(event)
                return
        self._blocked = True
        forceSelect = False
        sel = self.selectedItems()
        x, y = event.scenePos().x(), event.scenePos().y()
        if self._integerPlane:
            x, y = round(x), round(y)
        # XXX: not sure why isinstance does not work here
        if len(sel) == 1:
            isLastOnCurve = type(sel[0]) is OnCurvePointItem and sel[0]._contour.open and \
                sel[0].getPointIndex() == len(sel[0]._contour)-1
            # TODO: reimplement convenience methods in OffCurvePointItem
            isLastOffCurve = type(sel[0]) is OffCurvePointItem and sel[0].parentItem()._contour.open and \
                sel[0].parentItem().getPointIndex()+1 == len(sel[0].parentItem()._contour)-1
        if len(sel) == 1 and (isLastOffCurve or isLastOnCurve):
            if isLastOnCurve:
                lastContour = sel[0]._contour
            else:
                lastContour = sel[0].parentItem()._contour
            if (touched and isinstance(touched, OnCurvePointItem)) and touched.getPointIndex() == 0 \
                  and lastContour == touched._contour and len(lastContour) > 1:
                # Changing the first point from move to line/curve will cycle and so close the contour
                if isLastOffCurve:
                    lastContour.addPoint((x,y))
                    lastContour[0].segmentType = "curve"
                    touched.childItems()[1].setVisible(True)
                else:
                    lastContour[0].segmentType = "line"
            elif touched and isinstance(touched, OnCurvePointItem):
                super(GlyphScene, self).mousePressEvent(event)
                return
            else:
                if QApplication.keyboardModifiers() & Qt.ShiftModifier:
                    forceSelect = True
                    if isLastOnCurve:
                        refx = sel[0].x()
                        refy = sel[0].y()
                    else:
                        refx = sel[0].parentItem().x()
                        refy = sel[0].parentItem().y()
                    if abs(x-refx) > abs(y-refy): y = copysign(refy, y)
                    else: x = copysign(refx, x)
                if isLastOffCurve:
                    lastContour.addPoint((x,y))
                    lastContour.addPoint((x,y), "curve")
                else:
                    lastContour.addPoint((x,y), "line")
                item = OnCurvePointItem(x, y, False, lastContour, lastContour[-1], self.getViewScale())
                self.addItem(item)
                for _ in range(2):
                    lineObj = HandleLineItem(0, 0, 0, 0, item)
                    CPObject = OffCurvePointItem(0, 0, item)
                    CPObject.setVisible(False)
                if isLastOffCurve:
                    item.childItems()[1].setVisible(True)
            lastContour.dirty = True
            self._editing = True
        elif not (touched and isinstance(touched, OnCurvePointItem)):
            from defcon.objects.contour import Contour
            nextC = Contour()
            self._glyphObject.appendContour(nextC)
            nextC.addPoint((x,y), "move")

            item = OnCurvePointItem(x, y, False, self._glyphObject[-1], self._glyphObject[-1][-1], self.getViewScale())
            self.addItem(item)
            for _ in range(2):
                lineObj = HandleLineItem(0, 0, 0, 0, item)
                CPObject = OffCurvePointItem(0, 0, item)
                CPObject.setVisible(False)
            self._editing = True
        self._blocked = False
        super(GlyphScene, self).mousePressEvent(event)
        # Since shift clamps, we might be missing the point in mousePressEvent
        if forceSelect: item.setSelected(True)
    
    def mouseMoveEvent(self, event):
        if self._editing is True:
            sel = self.selectedItems()
            if len(sel) == 1:
                if isinstance(sel[0], OnCurvePointItem) and (event.scenePos() - sel[0].pos()).manhattanLength() >= 2:
                    mouseGrabberItem = self.mouseGrabberItem()
                    # If we drawn an onCurve w Shift and we're not touching the item, we wont have
                    # a mouse grabber (anyways), return early here.
                    if mouseGrabberItem is None:
                        event.accept()
                        return
                    self._blocked = True
                    if len(sel[0]._contour) < 2:
                        # release current onCurve
                        self.sendEvent(sel[0], QEvent(QEvent.MouseButtonRelease))
                        mouseGrabberItem.ungrabMouse()
                        sel[0].setSelected(False)
                        # append an offCurve point and start moving it
                        sel[0]._contour.addPoint((event.scenePos().x(), event.scenePos().y()))
                        nextCP = sel[0].childItems()[3]
                        nextCP.setVisible(True)
                        nextCP._needsUngrab = True
                        #nextCP.setSelected(True)
                        self.sendEvent(nextCP, QEvent(QEvent.MouseButtonPress))
                        nextCP.grabMouse()
                    else:
                        from defcon.objects.point import Point
                        # release current onCurve, delete from contour
                        self.sendEvent(sel[0], QEvent(QEvent.MouseButtonRelease))
                        mouseGrabberItem.ungrabMouse()
                        sel[0].setSelected(False)
                        
                        # construct a curve segment to the current point if there is not one
                        onCurve = sel[0]._point
                        if not onCurve.segmentType == "curve":
                            # remove the last onCurve
                            sel[0]._contour.removePoint(onCurve)
                            prev = sel[0]._contour[-1]
                            self.getItemForPoint(prev).childItems()[3].setVisible(True)
                            # add a zero-length offCurve to the previous point
                            sel[0]._contour.addPoint((prev.x, prev.y))
                            # add prevOffCurve and activate
                            sel[0]._contour.addPoint((sel[0].x(), sel[0].y()))
                            sel[0].childItems()[1].setVisible(True)
                            # add back current onCurve as a curve point
                            sel[0]._contour.addPoint((onCurve.x, onCurve.y), "curve")
                            sel[0]._point = sel[0]._contour[-1]
                        if not QApplication.keyboardModifiers() & Qt.AltModifier:
                            sel[0]._point.smooth = True
                            sel[0]._isSmooth = True
                            sel[0].setPointPath()
                        if sel[0].getPointIndex() == 0:
                            # we're probably dealing with the first point that we looped.
                            # preserve nextCP whatsoever.
                            lineObj = HandleLineItem(0, 0, 0, 0, sel[0])
                            nextCP = OffCurvePointItem(0, 0, sel[0])
                            # now we have l1, p1, l2, p2, l3, p3
                            l2 = sel[0].childItems()[2]
                            lineObj.stackBefore(l2)
                            nextCP.stackBefore(l2)
                        else:
                            # add last offCurve
                            sel[0]._contour.addPoint((sel[0].x(), sel[0].y()))
                            nextCP = sel[0].childItems()[3]
                        nextCP._needsUngrab = True
                        nextCP.setVisible(True)
                        #nextCP.setSelected(True)
                        self.sendEvent(nextCP, QEvent(QEvent.MouseButtonPress))
                        nextCP.grabMouse()
                    self._blocked = False
                    self._editing = None
                    super(GlyphScene, self).mouseMoveEvent(event)
                else:
                    # eat the event
                    event.accept()
        else:
            currentTool = self.views()[0]._currentTool
            if currentTool == SceneTools.RulerTool:
                self.rulerMouseMove(event)
                return
            items = self.items(event.scenePos())
            # XXX: we must cater w mouse tracking
            # we dont need isSelected() once its rid
            if len(items) > 1 and isinstance(items[0], OnCurvePointItem) and \
                  isinstance(items[1], OffCurvePointItem) and items[1].isSelected():
                items[1].setPos(0, 0)
            else:
                super(GlyphScene, self).mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._editing = False
        currentTool = self.views()[0]._currentTool
        if currentTool == SceneTools.DrawingTool:
            # cleanup extra point elements if we dealt w curved first point
            touched = self.itemAt(event.scenePos(), self.views()[0].transform())
            if touched and isinstance(touched, OffCurvePointItem):
                onCurve = touched.parentItem()
                children = onCurve.childItems()
                if len(children) > 4:
                    # l1, p1, l3, p3, l2, p2
                    children[3].prepareGeometryChange()
                    self.removeItem(children[3])
                    children[2].prepareGeometryChange()
                    self.removeItem(children[2])

                    onCurve._isSmooth = False
                    onCurve.setPointPath()
                    onCurve._point.smooth = False
        elif currentTool == SceneTools.RulerTool:
            self.rulerMouseRelease(event)
        super(GlyphScene, self).mouseReleaseEvent(event)
    
    def rulerMousePress(self, event):
        touched = self.itemAt(event.scenePos(), self.views()[0].transform())
        if touched is not None and isinstance(touched, OnCurvePointItem) or \
            isinstance(touched, OffCurvePointItem):
            x, y = touched.scenePos().x(), touched.scenePos().y()
        else:
            x, y = event.scenePos().x(), event.scenePos().y()
        if self._integerPlane:
            x, y = round(x), round(y)
        if self._cachedRuler is not None:
            self.removeItem(self._cachedRuler)
            self._cachedRuler = None
        path = QPainterPath()
        path.moveTo(x, y)
        path.lineTo(x+1, y)
        path.lineTo(x+1, y+1)
        path.closeSubpath()
        self._rulerObject = self.addPath(path)
        textItem = QGraphicsSimpleTextItem("0", self._rulerObject)
        font = self.font()
        font.setPointSize(9)
        textItem.setFont(font)
        textItem.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        textItem.setPos(x, y + textItem.boundingRect().height())
        event.accept()
    
    def rulerMouseMove(self, event):
        # XXX: shouldnt have to do this, it seems mouseTracking is wrongly activated
        if self._rulerObject is None: return
        touched = self.itemAt(event.scenePos(), self.views()[0].transform())
        if touched is not None and isinstance(touched, OnCurvePointItem) or \
            isinstance(touched, OffCurvePointItem):
            x, y = touched.scenePos().x(), touched.scenePos().y()
        else:
            # TODO: 45deg clamp w ShiftModifier
            # maybe make a function for that + other occurences...
            x, y = event.scenePos().x(), event.scenePos().y()
        if self._integerPlane:
            x, y = round(x), round(y)
        path = self._rulerObject.path()
        baseElem = path.elementAt(0)
        path.setElementPositionAt(1, x, baseElem.y)
        path.setElementPositionAt(2, x, y)
        path.setElementPositionAt(3, baseElem.x, baseElem.y)
        self._rulerObject.setPath(path)
        textItem = self._rulerObject.childItems()[0]
        line = QLineF(baseElem.x, baseElem.y, x, y)
        l = line.length()
        # XXX: angle() doesnt go by trigonometric direction. Weird.
        # TODO: maybe split in positive/negative 180s (ff)
        a = 360 - line.angle()
        line.setP2(QPointF(x, baseElem.y))
        h = line.length()
        line.setP1(QPointF(x, y))
        v = line.length()
        text = "%d\n↔ %d\n↕ %d\nα %dº" % (l, h, v, a)
        textItem.setText(text)
        dx = x - baseElem.x
        if dx >= 0: px = x
        else: px = x - textItem.boundingRect().width()
        dy = y - baseElem.y
        if dy > 0: py = baseElem.y
        else: py = baseElem.y + textItem.boundingRect().height()
        textItem.setPos(px, py)
        event.accept()
    
    def rulerMouseRelease(self, event):
        self._cachedRuler = self._rulerObject
        self._rulerObject = None
        event.accept()

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
        
        self._inverseScale = 0.1
        self._scale = 10
        self._noPointSizePadding = 200
        self._bluesColor = QColor.fromRgbF(.5, .7, 1, .3)
        self._drawStroke = True
        self._showOffCurvePoints = True
        self._showOnCurvePoints = True
        self._fillColor = QColor.fromRgbF(0, 0, 0, .4)
        self._componentFillColor = QColor.fromRgbF(.2, .2, .3, .4)
        self._showMetricsTitles = True
        self._metricsColor = QColor(70, 70, 70)

        self.setBackgroundBrush(QBrush(Qt.lightGray))
        self.setScene(GlyphScene(self))
        font = self.font()
        font.setFamily("Roboto Mono")
        font.setFixedPitch(True)
        self.setFont(font)
        
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        #self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        
        self._drawingTool = SceneTools.SelectionTool
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        self.setRenderHint(QPainter.Antialiasing)
        #self.translate(0, self.height()*(1+self._font.info.descender/self._font.info.unitsPerEm))
        self.scale(1, -1)
        self.addBackground()
        self.addBlues()
        self.addHorizontalMetrics()
        self.addOutlines()
        self.addPoints()
    
    def _glyphChanged(self, notification):
        # TODO: maybe detect sidebearing changes (space center) and then only
        # translate elements rather than reconstructing them.
        # Also we lose selection when reconstructing, rf does not when changing
        # sp.center values.
        path = self._glyph.getRepresentation("defconQt.NoComponentsQPainterPath")
        scene = self.scene()
        scene._outlineItem.setPath(path)
        #scene._outlineItem.update()
        if not scene._blocked:
            # TODO: also rewind anchors and components
            for item in scene.items():
                if isinstance(item, OnCurvePointItem):
                    scene.removeItem(item)
            self.addPoints()
            # For now, we'll assume not scene._blocked == moving UI points
            # this will not be the case anymore when drag sidebearings pops up
            scene._widthItem.setRect(0, -1000, self._glyph.width, 3000)

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
        scene = self.scene()
        width = self._glyph.width
        item = scene.addRect(-1000, -1000, 3000, 3000, QPen(Qt.black), QBrush(Qt.gray))
        item.setZValue(-1000)
        scene._widthItem = scene.addRect(0, -1000, width, 3000, QPen(Qt.NoPen), QBrush(backgroundColor))
        scene._widthItem.setZValue(-999)
        self.centerOn(width/2, self._font.info.descender+self._font.info.unitsPerEm/2)
    
    def addBlues(self):
        scene = self.scene()
        #width = self._glyph.width# * self._inverseScale
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
                if yMin == yMax:
                    item = scene.addLine(-1000, yMin, 3000, yMax, QPen(self._bluesColor))
                    item.setZValue(-998)
                else:
                    item = scene.addRect(-1000, yMin, 3000, yMax - yMin, QPen(Qt.NoPen), QBrush(self._bluesColor))
                    item.setZValue(-998)
    
    def addHorizontalMetrics(self):
        scene = self.scene()
        width = self._glyph.width# * self._inverseScale
        toDraw = [
            ("Descender", self._font.info.descender),
            ("Baseline", 0),
            ("x-height", self._font.info.xHeight),
            ("Cap height", self._font.info.capHeight),
            ("Ascender", self._font.info.ascender)
        ]
        positions = {}
        for name, position in toDraw:
            if position not in positions:
                positions[position] = []
            positions[position].append(name)
        # lines
        for position, names in sorted(positions.items()):
            y = self.roundPosition(position)
            item = scene.addLine(-1000, y, 2000, y, QPen(self._metricsColor))
            item.setZValue(-997)
        # text
        if self._showMetricsTitles:# and self._impliedPointSize > 150:
            fontSize = 9# * self._inverseScale
            font = self.font()
            font.setPointSize(fontSize)
            for position, names in sorted(positions.items()):
                y = position - (fontSize / 2)
                text = ", ".join(names)
                text = " %s " % text
                item = scene.addSimpleText(text, font)
                item.setBrush(self._metricsColor)
                item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
                item.setPos(width, y) # XXX
                item.setZValue(-997)

    def addOutlines(self):
        scene = self.scene()
        # outlines
        path = self._glyph.getRepresentation("defconQt.NoComponentsQPainterPath")
        scene._outlineItem = scene.addPath(path, brush=QBrush(self._fillColor))
        scene._outlineItem.setZValue(-995)
        scene._glyphObject = self._glyph
        # components
        path = self._glyph.getRepresentation("defconQt.OnlyComponentsQPainterPath")
        scene.addPath(path, brush=QBrush(self._componentFillColor))

    def addPoints(self):
        scene = self.scene()
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
        '''
        if pointSize > 250:
            coordinateSize = 9
        else:
            coordinateSize = 0
        '''
        # use the data from the outline representation
        outlineData = self._glyph.getRepresentation("defconQt.OutlineInformation")
        points = [] # TODO: remove this unless we need it # useful for text drawing, add it
        startObjects = []
        scale = self.transform().m11()
        if outlineData["onCurvePoints"]:
            for onCurve in outlineData["onCurvePoints"]:
                # on curve
                x, y = onCurve.x, onCurve.y
                points.append((x, y))
                item = OnCurvePointItem(x, y, onCurve.isSmooth, self._glyph[onCurve.contourIndex],
                    self._glyph[onCurve.contourIndex][onCurve.pointIndex], scale)
                scene.addItem(item)
                # off curve
                for CP in [onCurve.prevCP, onCurve.nextCP]:
                    if CP:
                        cx, cy = CP
                        # line
                        lineObj = HandleLineItem(0, 0, cx-x, cy-y, item)
                        # point
                        points.append((cx, cy))
                        CPObject = OffCurvePointItem(cx-x, cy-y, item)
                    else:
                        lineObj = HandleLineItem(0, 0, 0, 0, item)
                        #lineObj.setVisible(False)
                        CPObject = OffCurvePointItem(0, 0, item)
                        CPObject.setVisible(False)
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
                    item = scene.addPath(path, QPen(Qt.NoPen), QBrush(self._startPointColor))
                    startObjects.append(item)
                    #path.closeSubpath()
                else:
                    item = scene.addEllipse(x-startHalf, y-startHalf, startWidth, startHeight,
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
            dragMode = self.dragMode()
            if dragMode == QGraphicsView.RubberBandDrag:
                self.setDragMode(QGraphicsView.ScrollHandDrag)
            elif dragMode == QGraphicsView.ScrollHandDrag:
                self.setDragMode(QGraphicsView.RubberBandDrag)
        super(GlyphView, self).mousePressEvent(event)

    def setSceneDrawing(self):
        self._currentTool = SceneTools.DrawingTool
        self.setDragMode(QGraphicsView.NoDrag)
    
    def setSceneRuler(self):
        self._currentTool = SceneTools.RulerTool
        self.setDragMode(QGraphicsView.NoDrag)
    
    def setSceneSelection(self):
        self._currentTool = SceneTools.SelectionTool
        self.setDragMode(QGraphicsView.RubberBandDrag)
    
    # Lock/release handdrag does not seem to work…
    '''
    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.MidButton):
            self.setDragMode(QGraphicsView.RubberBandDrag)
        super(GlyphView, self).mouseReleaseEvent(event)
    '''

    def wheelEvent(self, event):
        factor = pow(1.2, event.angleDelta().y() / 120.0)

        #self._calcScale()
        #self._setFrame()
        self.scale(factor, factor)
        # TODO: stop displaying SimpleTextItems at certains sizes, maybe anchor them differently as well
        scale = self.transform().m11()
        if scale < 4:
            for item in self.scene().items():
                if isinstance(item, OnCurvePointItem) or isinstance(item, OffCurvePointItem) or \
                  isinstance(item, ResizeHandleItem):
                    item.setPointPath(scale)
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
