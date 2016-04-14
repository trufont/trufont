from PyQt5.QtWidgets import QApplication
from trufont.drawingTools.baseButton import BaseButton


def removeSelectionOverlap(glyph):
    # unselected bookkeeping
    unselContours = []
    for contour in glyph:
        if not contour.selection:
            unselContours.append(contour)
    partialSelection = unselContours and len(unselContours) < len(glyph)
    if partialSelection:
        for contour in reversed(unselContours):
            glyph.removeContour(contour)
    glyph.removeOverlap()
    if partialSelection:
        for contour in unselContours:
            glyph.appendContour(contour)


class RemoveOverlapButton(BaseButton):
    name = QApplication.translate("RemoveOverlapButton", "Remove Overlap")
    iconPath = ":union.svg"

    def clicked(self):
        removeSelectionOverlap(self._glyph)
