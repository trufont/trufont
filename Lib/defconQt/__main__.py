from defconQt import __version__, representationFactories
from defconQt import icons_db  # noqa
from defconQt.fontView import Application
from PyQt5.QtCore import (
    QCommandLineParser, QSettings, QTranslator, QLocale,
    QLibraryInfo)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
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

    # Qt's translation for itself. May not be installed.
    qtTranslator = QTranslator()
    qtTranslator.load("qt_" + QLocale.system().name(),
                      QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qtTranslator)

    appTranslator = QTranslator()
    appTranslator.load("trufont_" + QLocale.system().name(),
                       os.path.dirname(os.path.realpath(__file__)) +
                       "/resources")
    app.installTranslator(appTranslator)

    # parse options and open fonts
    parser = QCommandLineParser()
    parser.setApplicationDescription(QApplication.translate(
        "Command-line parser", "The TruFont font editor."))
    parser.addHelpOption()
    parser.addVersionOption()
    parser.addPositionalArgument(QApplication.translate(
        "Command-line parser", "files"), QApplication.translate(
        "Command-line parser", "The UFO files to open."))
    parser.process(app)
    args = parser.positionalArguments()
    if not len(args):
        fontPath = None
        # maybe load recent file
        settings = QSettings()
        loadRecentFile = settings.value("misc/loadRecentFile", False, bool)
        if loadRecentFile:
            recentFiles = settings.value("core/recentFiles", [], type=str)
            if len(recentFiles) and os.path.exists(recentFiles[0]):
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
