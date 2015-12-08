from defconQt.tools.baseButton import BaseButton


class RemoveOverlapButton(BaseButton):
    name = "Remove Overlap"
    iconPath = ":resources/union.svg"

    def clicked(self):
        self._glyph.removeOverlap()
