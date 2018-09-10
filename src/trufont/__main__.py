import sys
import trufont
from trufont.objects import factories
from trufont.objects.application import Application
import wx


def main():
    app = wx.App()
    app.SetAppDisplayName("TruFont")
    app.fileHistory = wx.FileHistory()
    factories.registerAllFactories()
    # could just create the object in __init__ and set app
    # here, this would avoid the trufont.TruFont.xxx all over the place
    trufont.TruFont = TruFont = Application(app)
    TruFont.newFont()
    sys.exit(app.MainLoop())


if __name__ == "__main__":
    main()
