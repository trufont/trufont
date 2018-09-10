import trufont
from trufont.drawingTools.baseTool import BaseTool
from trufont.util.drawing import CreatePath
import unicodedata
import wx
from wx import GetTranslation as tr

_path = CreatePath()
_path.MoveToPoint(2.87, 4.98)
_path.AddLineToPoint(3.17, 2.472)
_path.AddLineToPoint(3.46, 2.153)
_path.AddLineToPoint(6.836, 2.153)
_path.AddLineToPoint(6.836, 13.47)
_path.AddLineToPoint(6.454, 13.77)
_path.AddLineToPoint(4.82, 13.9)
_path.AddLineToPoint(4.82, 15.0)
_path.AddLineToPoint(11.12, 15.0)
_path.AddLineToPoint(11.12, 13.9)
_path.AddLineToPoint(9.485, 13.77)
_path.AddLineToPoint(9.103, 13.47)
_path.AddLineToPoint(9.103, 2.155)
_path.AddLineToPoint(12.48, 2.155)
_path.AddLineToPoint(12.77, 2.474)
_path.AddLineToPoint(13.07, 4.982)
_path.AddLineToPoint(14.45, 4.982)
_path.AddLineToPoint(14.45, 1.0)
_path.AddLineToPoint(1.49, 1.0)
_path.AddLineToPoint(1.49, 4.98)
_path.CloseSubpath()


def _isUnicodeChar(text):
        return len(text) and unicodedata.category(text) != "Cc"


class TextTool(BaseTool):
    icon = _path
    name = tr("Text")
    shortcut = "T"
    grabKeyboard = True

    @property
    def cursor(self):
        return wx.Cursor(wx.CURSOR_IBEAM)

    def drawingAttribute(self, attr):
        # maybe we should just go back to GetDrawingAttribute/GetDrawingColor?
        if attr == "showFill" or attr == "showTextCursor" or attr == "showTextMetrics":
            return True
        elif attr.startswith("show"):
            return False
        elif attr.endswith("Color"):
            return wx.BLACK
        return None

    def OnToolActivated(self):
        self.canvas.Refresh()

    def OnToolDisabled(self):
        self.canvas.Refresh()

    # events

    def OnChar(self, event):
        self.canvas.textCursor.insertText(chr(event.GetUnicodeKey()))

    def OnKeyDown(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_CONTROL_V:
            clipboard = wx.Clipboard.Get()
            if clipboard.Open():
                if clipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                    data = wx.TextDataObject()
                    clipboard.GetData(data)
                    self.canvas.textCursor.insertText(data.GetText())
                clipboard.Close()
        # ! attn on mac etc. physical keyboard layout is different so we
        # probably wanna use Ctrl (Meta) instead of Command
        elif (event.ControlDown() or event.AltDown()) and \
                (key == wx.WXK_LEFT or key == wx.WXK_RIGHT):
            layer = self.layer
            if layer is None:
                return
            dx = 1
            if event.ShiftDown():
                dx *= 10
            if key == wx.WXK_LEFT:
                dx = -dx
            if event.ControlDown() and layer.leftMargin is not None:
                layer.leftMargin += dx
            else:
                layer.width += dx
            trufont.TruFont.updateUI()
        elif key == wx.WXK_LEFT:
            self.canvas.textCursor.movePosition("left")
        elif key == wx.WXK_RIGHT:
            self.canvas.textCursor.movePosition("right")
        elif key == wx.WXK_DELETE:
            self.canvas.textCursor.deleteChar()
        elif key == wx.WXK_BACK:
            self.canvas.textCursor.deletePreviousChar()
        else:
            event.Skip()

    def OnMouseDClick(self, event):
        if event.LeftDClick():
            canvas = self.canvas
            canvas.moveTextCursorTo(event.GetPosition())
            # bring back selection tool
            wx.GetTopLevelParent(canvas).resetToolBar()
        else:
            super().OnMouseDClick(event)

    def OnMouseDown(self, event):
        if event.LeftDown():
            canvas = self.canvas
            canvas.moveTextCursorTo(event.GetPosition(), lOffset=True)
            canvas.SetFocus()
        else:
            super().OnMouseDown(event)
