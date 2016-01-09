from defconQt import __version__, representationFactories
from defconQt import icons_db  # noqa
from defconQt.fontView import Application, MainWindow
from defconQt.objects.defcon import TFont
import sys
import os
from PyQt5.QtCore import QCommandLineParser, QSettings
from PyQt5.QtGui import QIcon


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
        window = MainWindow(None)
        window.show()
    else:
        for arg in args:
            font = TFont(os.path.abspath(arg))
            window = MainWindow(font)
            window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
