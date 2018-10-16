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

    # check sys.argv
    _debug = False
    _log = False
    for arg in sys.argv[1:]:
        if "debug" in arg.lower():
            _debug = True
        elif "loggingrotate" in arg.lower():
            _log = True 

    trufont.TruFont = TruFont = Application(app, _debug, _log)
    TruFont.newFont()
    sys.exit(app.MainLoop())


if __name__ == "__main__":
    main()
