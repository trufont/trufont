import os
from trufont import __file__ as modulePath
import wx

modulePath = os.path.dirname(modulePath)


def GetUserIcon(name, width, height, parent):
    scale = parent.GetContentScaleFactor()
    width *= scale
    height *= scale
    path = os.path.join(modulePath, "resources", name)
    img = wx.Image(path)
    bmp = img.Scale(width, height, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
    return wx.Icon(bmp)
