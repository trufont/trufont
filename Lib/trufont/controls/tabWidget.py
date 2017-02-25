from PyQt5.QtCore import pyqtSignal, QEvent, QRect, QSize, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath
from PyQt5.QtWidgets import QSizePolicy, QToolTip, QWidget

__all__ = ["TabWidget"]

sidePadding = 9
spacing = 2
tabPadding = 1
topPadding = bottomPadding = 5
crossMargin = sidePadding
crossSize = 7

cross = QPainterPath()
cross.moveTo(0.38, 0.38)
cross.lineTo(9.63, 9.63)
cross.moveTo(0.38, 9.63)
cross.lineTo(9.63, 0.38)


class TabWidget(QWidget):
    """
    # TODO: RTL support?
    # TODO: need a sound toolbar API: tools, placement, scope
    #      look into QToolBar, QAction
    """
    currentTabChanged = pyqtSignal(int)
    tabRemoved = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self._currentTab = None
        self._heroFirstTab = False
        self._hoverClose = None
        self._hoverTab = None
        self._tabs = []
        self._textWidth = 148

    def addTab(self, name, parent=None):
        self._tabs.append(name)
        self._recalcTextWidth()
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
        self._recalcTextWidth()
        self.update()

    def setTabName(self, index, name):
        self._tabs[index] = name
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

    def _recalcTextWidth(self):
        count = len(self._tabs)
        maxTextWidth = self.width() - count * (
            2 * sidePadding + crossMargin + crossSize) - (count - 1) * spacing
        self._textWidth = min(round(maxTextWidth / count), 148)
        # TODO: heroFirstTab is not accounted for

    # ----------
    # Qt methods
    # ----------

    def event(self, event):
        if False and event.type() == QEvent.ToolTip:
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
            self._hoverTab, self._hoverClose)
        if all(i is None for i in elements):
            return
        self._hoverTab = self._hoverClose = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = self.fontMetrics()

        # tabs
        self._closeRects = {}
        self._tabsRects = {}
        painter.save()
        currentTab = self.currentTab()
        tabFillColor = QColor(240, 240, 240)
        hoverFillColor = QColor(253, 253, 255)
        textHeight = metrics.lineSpacing()
        left = 0
        h = textHeight + topPadding * 2
        for index, name in enumerate(self.tabs()):
            isHeroFirstTab = not index and self._heroFirstTab
            isClosable = not isHeroFirstTab
            textWidth = self._textWidth
            w = sidePadding * 2 + textWidth
            if isClosable:
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
                if fillColor.lightness() < 156:
                    textColor = Qt.white
            elif index == currentTab:
                fillColor = tabFillColor
            elif index == self._hoverTab:
                fillColor = hoverFillColor
            else:
                fillColor = None
            if fillColor is not None:
                painter.fillRect(0, 0, w, h, fillColor)
            # text
            painter.save()
            painter.translate(sidePadding, metrics.ascent() + topPadding)
            painter.setPen(textColor)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.drawText(0, 0, name)
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
                    color = QColor(78, 78, 78)
                painter.setPen(color)
                pen = painter.pen()
                pen.setWidthF(1.5)
                painter.setPen(pen)
                painter.translate(textWidth + sidePadding, -crossSize)
                painter.setClipRect(0, 0, crossSize, crossSize)
                painter.scale(crossSize / 10, crossSize / 10)
                painter.drawPath(cross)
            painter.restore()
            # shift for the next tab
            shift = textWidth + 2 * sidePadding + spacing
            if not isHeroFirstTab:
                shift += tabPadding
            if isClosable:
                shift += crossMargin + crossSize
            painter.translate(shift, 0)
            left += shift
        painter.restore()

    def minimumSizeHint(self):
        height = topPadding + bottomPadding + self.fontMetrics().lineSpacing()
        return QSize(400, height)

    def sizeHint(self):
        width = 0
        metrics = self.fontMetrics()
        heroTab = self._heroFirstTab
        for name in self._tabs:
            width += metrics.width(name) + 2 * sidePadding + tabPadding
            if not heroTab:
                width += crossMargin + crossSize
            heroTab = False
        height = topPadding + bottomPadding + metrics.lineSpacing()
        return QSize(width, height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recalcTextWidth()
