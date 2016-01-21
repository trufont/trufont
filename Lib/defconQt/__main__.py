from defconQt import __version__, representationFactories
from defconQt import icons_db  # noqa
from defconQt.fontView import Application
from PyQt5.QtCore import QCommandLineParser, QSettings
from PyQt5.QtGui import QIcon
import os
import sys


def main():
    # register representation factories
    representationFactories.registerAllFactories()
    # initialize the app
    app = Application(sys.argv)
    app.setOrganizationName("TruFont")
    app.setOrganizationDomain("trufont.github.io")
    app.setApplicationName("TruFont")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(":/resources/app.png"))
    settings = QSettings()
    glyphListPath = settings.value("settings/glyphListPath", "", type=str)
    if glyphListPath and os.path.exists(glyphListPath):
        from defconQt.util import glyphList
        try:
            glyphList = glyphList.parseGlyphList(glyphListPath)
        except Exception as e:
            print(e)
        else:
            app.GL2UV = glyphList
    # parse options and open fonts
    parser = QCommandLineParser()
    parser.setApplicationDescription("The TruFont font editor.")
    parser.addHelpOption()
    parser.addVersionOption()
    parser.addPositionalArgument("files", "The UFO files to open.")
    parser.process(app)
    args = parser.positionalArguments()
    if not len(args):
        fontPath = None
        # maybe load recent file
        settings = QSettings()
        loadRecentFile = settings.value("misc/loadRecentFile", False, bool)
        if loadRecentFile:
            recentFiles = settings.value("core/recentFiles", [], type=str)
            if len(recentFiles):
                fontPath = recentFiles[0]
                app.openFile(fontPath)
        # otherwise, create a new file
        if fontPath is None:
            app.newFile()
    else:
        for fontPath in args:
            app.openFile(fontPath)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
