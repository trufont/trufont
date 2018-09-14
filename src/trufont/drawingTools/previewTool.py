from trufont.drawingTools.baseTool import BaseTool
import wx


class PreviewTool(BaseTool):
    def drawingAttribute(self, attr):
        if attr == "showFill":
            return True
        elif attr.startswith("show"):
            return False
        elif attr.endswith("Color"):
            return wx.BLACK
        return None
