from PyQt5.QtCore import pyqtSignal, QEvent, QRect, QSize, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath
from PyQt5.QtWidgets import QSizePolicy, QToolTip, QWidget
from trufont.tools import platformSpecific

__all__ = ["ShellWidget"]

sidePadding = 14
tabPadding = 1
topPadding = bottomPadding = 6
crossMargin = 10
crossScale = .83

toolIconSize = 28
sideToolPadding = 6
toolPadding = 0
topToolPadding = bottomToolPadding = 7

cross = QPainterPath()
cross.moveTo(0.38, 0.38)
cross.lineTo(9.63, 9.63)
cross.moveTo(0.38, 9.63)
cross.lineTo(9.63, 0.38)


class Tab(object):
    def __init__(self, name, tools, parent=None):
        self.name = name
        self.tools = tools
        self.parent = parent


class ShellWidget(QWidget):
    """
    # TODO: RTL support?
    # TODO: need a sound toolbar API: tools, placement, scope
    #      look into QToolBar, QAction
    """
    currentTabChanged = pyqtSignal(int)
    currentToolChanged = pyqtSignal(object)
    persistentToolToggled = pyqtSignal(int)
    tabRemoved = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self._currentTab = None
        self._currentTool = None
        self._heroFirstTab = False
        self._hoverClose = None
        self._hoverTab = None
        self._hoverTool = None
        self._hoverPersistentTool = None
        self._tabs = []
        self._persistentTools = []
        self._toolsClasses = []

    def addTab(self, name, parent=None):
        if self._heroFirstTab and not self._tabs:
            tools = []
        else:
            tools = [cls_(parent=parent) for cls_ in self._toolsClasses]
        self._tabs.append(Tab(name, tools, parent))
        self.update()

    def removeTab(self, index):
        del self._tabs[index]
        if self._currentTab >= index:
            if self._tabs:
                self._currentTab -= 1
            else:
                self._currentTab = None
            self.currentTabChanged.emit(self._currentTab)
        if len(self._tabs) <= self._heroFirstTab:
            self._currentTool = None
        self.tabRemoved.emit(index)
        # XXX: somewhat hackish, we have no way to compute new rects except
        # post-repaint
        # idea: reuse rects but translate by removed tab width after tab index
        self._hoverClose = None
        self.update()

    def setTabName(self, index, name):
        tab = self._tabs[index]
        tab.name = name
        self.update()

    def toolsClasses(self):
        return self._toolsClasses

    def setToolsClasses(self, classes):
        if self._tabs:
            return
        self._toolsClasses = list(classes)

    def addToolClass(self, cls):
        self._toolsClasses.append(cls)
        for tab in self._tabs[int(self._heroFirstTab):]:
            # TODO: kinda lame to have to call tab.parent which itself
            # we store in the tab.
            tab.tools.append(cls(parent=tab.parent))
        self.update()

    def removeToolClass(self, cls):
        self._toolsClasses.remove(cls)
        for tab in self._tabs:
            for tool in tab.tools:
                if isinstance(tool, cls):
                    tab.tools.remove(tool)
                    break
        self.update()

    def currentTab(self):
        if self._currentTab is None and self._tabs:
            self._currentTab = 0
        return self._currentTab

    def setCurrentTab(self, value):
        if value < 0:
            value = value % len(self._tabs)
        if self._currentTab == value:
            return
        self._currentTab = value
        self.currentTabChanged.emit(self._currentTab)
        self.update()

    def heroFirstTab(self):
        return self._heroFirstTab

    def setHeroFirstTab(self, value):
        if self._tabs:
            return
        self._heroFirstTab = value

    def tabs(self):
        return self._tabs

    def currentTool(self):
        if self._currentTool is None and len(
                self._tabs) > self._heroFirstTab and self._toolsClasses:
            self._currentTool = 0
        return self._currentTool

    def setCurrentTool(self, value):
        if value >= len(self._toolsClasses):
            return
        if self._currentTool == value:
            return
        self._currentTool = value
        self.updateTool()
        self.update()

    def updateTool(self):
        if self._currentTab is None:
            return
        tab = self._tabs[self._currentTab]
        currentTool = self.currentTool()
        if currentTool is None:
            return
        self.currentToolChanged.emit(tab.tools[currentTool])

    def persistentTools(self):
        return self._persistentTools

    def setPersistentTools(self, tools):
        self._persistentTools = tools
        self.update()

    def setPersistentToolEnabled(self, index, value):
        tool = self._persistentTools[index]
        if tool.activated == value:
            return
        tool.activated = value
        self.update()

    def togglePersistentTool(self, value):
        tool = self._persistentTools[value]
        tool.activated = not tool.activated
        self.persistentToolToggled.emit(value)
        self.update()

    # ----------
    # Qt methods
    # ----------

    def event(self, event):
        if event.type() == QEvent.ToolTip:
            for recordIndex, rect in self._toolsRects.items():
                if QRect(*rect).contains(event.pos()):
                    QToolTip.showText(event.globalPos(
                        ), self._toolsClasses[recordIndex].name)
            return True
        return super().event(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for recordIndex, rect in self._tabsRects.items():
                if QRect(*rect).contains(event.pos()):
                    self.setCurrentTab(recordIndex)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not hasattr(self, "_tabsRects"):
            return
        elements = [
            (self._closeRects, "_hoverClose"),
            (self._tabsRects, "_hoverTab"),
            (self._toolsRects, "_hoverTool"),
            (self._persistentToolsRects, "_hoverPersistentTool"),
        ]
        changed = False
        for rects, attr in elements:
            selected = None
            for recordIndex, rect in rects.items():
                if QRect(*rect).contains(event.pos()):
                    selected = recordIndex
                    break
            if getattr(self, attr) != selected:
                setattr(self, attr, selected)
                changed = True
        if changed:
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            elements = [
                (self._closeRects, self.removeTab),
                (self._toolsRects, self.setCurrentTool),
                (self._persistentToolsRects, self.togglePersistentTool),
            ]
            for rects, func in elements:
                for recordIndex, rect in rects.items():
                    if QRect(*rect).contains(event.pos()):
                        func(recordIndex)
                        return
        else:
            super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        elements = (
            self._hoverTab, self._hoverTool, self._hoverClose,
            self._hoverPersistentTool)
        if all(i is None for i in elements):
            return
        self._hoverTab = self._hoverTool = self._hoverClose = \
            self._hoverPersistentTool = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = self.fontMetrics()

        # init
        if platformSpecific.topBackground():
            painter.fillRect(event.rect(), Qt.white)
        # tabs
        self._closeRects = {}
        self._tabsRects = {}
        painter.save()
        currentTab = self.currentTab()
        tabFillColor = QColor(245, 246, 247)
        tabStrokeColor = QColor(218, 219, 220)
        hoverFillColor = QColor(253, 253, 255)
        hoverStrokeColor = QColor(235, 236, 236)
        textHeight = metrics.lineSpacing()
        left = 0
        h = textHeight + topPadding * 2
        for index, tab in enumerate(self.tabs()):
            isHeroFirstTab = not index and self._heroFirstTab
            isClosable = not isHeroFirstTab
            textWidth = metrics.width(tab.name)
            w = sidePadding * 2 + textWidth
            if isClosable:
                try:
                    crossSize
                except NameError:
                    crossSize = round(crossScale * metrics.ascent())
                w += crossMargin + crossSize
            self._tabsRects[index] = (left, 0, w, h)

            # background
            textColor = QColor(72, 72, 72)
            if isHeroFirstTab:
                if index == currentTab:
                    fillColor = QColor(18, 104, 179)
                elif index == self._hoverTab:
                    fillColor = QColor(41, 140, 225)
                else:
                    fillColor = QColor(25, 121, 202)
                strokeColor = None
                if fillColor.lightness() < 156:
                    textColor = Qt.white
            elif index == currentTab:
                fillColor = tabFillColor
                strokeColor = tabStrokeColor
            elif index == self._hoverTab:
                fillColor = hoverFillColor
                strokeColor = hoverStrokeColor
            else:
                fillColor = strokeColor = None
            if fillColor is not None:
                painter.fillRect(0, 0, w, h, fillColor)
            if strokeColor is not None:
                painter.save()
                painter.setPen(strokeColor)
                painter.drawLine(0, 0, 0, h)
                painter.drawLine(0, 0, w - 1, 0)
                painter.drawLine(w - 1, 0, w - 1, h)
                painter.restore()
            # text
            painter.save()
            painter.translate(sidePadding, metrics.ascent() + topPadding)
            painter.setPen(textColor)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.drawText(0, 0, tab.name)
            # cross
            if isClosable:
                # 3px padding for click rect
                self._closeRects[index] = (
                    left + textWidth + 2 * sidePadding - 3,
                    metrics.ascent() + topPadding - crossSize - 3,
                    crossSize + 6, crossSize + 6)
                if index == self._hoverClose:
                    color = QColor(254, 28, 28)
                else:
                    color = QColor(75, 75, 75)
                painter.setPen(color)
                pen = painter.pen()
                pen.setWidthF(1.1)
                painter.setPen(pen)
                painter.translate(textWidth + sidePadding, -crossSize)
                painter.setClipRect(0, 0, crossSize, crossSize)
                painter.scale(crossSize / 10, crossSize / 10)
                painter.drawPath(cross)
            painter.restore()
            # shift for the next tab
            shift = textWidth + 2 * sidePadding
            if not isHeroFirstTab:
                shift += tabPadding
            if isClosable:
                shift += crossMargin + crossSize
            painter.translate(shift, 0)
            left += shift
        painter.restore()

        # toolbar
        painter.save()
        painter.translate(0, h)
        if currentTab is None:
            return
        tab = self._tabs[currentTab]
        tabRect = self._tabsRects[currentTab]
        h, w = toolIconSize + topToolPadding * 2, self.width()
        # background
        painter.save()
        if False and not currentTab and self._heroFirstTab:
            fillColor = tabFillColor
            strokeColor = QColor(18, 104, 179)
        else:
            fillColor = tabFillColor
            strokeColor = tabStrokeColor
        painter.fillRect(0, 0, w, h, fillColor)
        if strokeColor is not None:
            painter.setPen(strokeColor)
            painter.drawLine(0, 0, tabRect[0], 0)
            painter.drawLine(tabRect[0] + tabRect[2] - 1, 0, w, 0)
            painter.drawLine(0, h - 1, w, h - 1)
        painter.restore()
        # tools
        self._toolsRects = {}
        path_ = QPainterPath()
        path_.addRoundedRect(0, 0, toolIconSize, toolIconSize, 3, 3)
        painter.save()
        left = sideToolPadding
        painter.translate(left, toolIconSize + topToolPadding)
        painter.scale(1, -1)
        painter.setRenderHint(QPainter.Antialiasing)
        # tab tools
        for index, tool in enumerate(tab.tools):
            if index == self._currentTool:
                painter.fillPath(path_, QColor(210, 214, 219))
            elif index == self._hoverTool:
                painter.fillPath(path_, QColor(221, 229, 238))
            self._toolsRects[index] = (
                left, toolIconSize + topToolPadding, toolIconSize,
                toolIconSize)
            painter.save()
            painter.setClipRect(4, 4, toolIconSize-4, toolIconSize-4)
            painter.fillPath(tool.icon, QColor(90, 90, 90))
            painter.restore()
            # XXX: tool.name, tooltip?
            painter.translate(toolIconSize + sideToolPadding, 0)
            left += toolIconSize + sideToolPadding
        painter.translate(-left, 0)
        left = self.width() - (
            sideToolPadding + toolIconSize) * len(self._persistentTools)
        painter.translate(left, 0)
        self._persistentToolsRects = {}
        for index, tool in enumerate(self._persistentTools):
            if tool.activated:
                painter.fillPath(path_, QColor(210, 214, 219))
            elif index == self._hoverPersistentTool:
                painter.fillPath(path_, QColor(221, 229, 238))
            self._persistentToolsRects[index] = (
                left, toolIconSize + topToolPadding, toolIconSize,
                toolIconSize)
            painter.fillPath(tool.icon, QColor(90, 90, 90))
            painter.translate(toolIconSize + sideToolPadding, 0)
            left += toolIconSize + sideToolPadding
        painter.restore()
        painter.restore()

    def minimumSizeHint(self):
        height = topPadding + bottomPadding + self.fontMetrics().lineSpacing()
        height += toolIconSize + topToolPadding * 2
        return QSize(400, height)

    def sizeHint(self):
        width = 0
        metrics = self.fontMetrics()
        heroTab = self._heroFirstTab
        for tab in self._tabs:
            width += metrics.width(tab.name) + 2 * sidePadding + tabPadding
            if not heroTab:
                width += crossMargin + round(crossScale * metrics.ascent())
            heroTab = False
        height = topPadding + bottomPadding + metrics.lineSpacing()
        height += toolIconSize + topToolPadding * 2
        return QSize(width, height)
