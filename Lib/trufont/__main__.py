from defconQt import representationFactories as baseRepresentationFactories
from trufont import __version__, representationFactories
from trufont.objects.application import Application
from trufont.resources import icons_db  # noqa
from trufont.windows.outputWindow import OutputWindow
from PyQt5.QtCore import (
    Qt, QCommandLineParser, QSettings, QTranslator, QLocale, QLibraryInfo)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
import os
import sys
import traceback

_showMessages = True


def main():
    global app
    # register representation factories
    baseRepresentationFactories.registerAllFactories()
    representationFactories.registerAllFactories()
    # initialize the app
    app = Application(sys.argv)
    app.setOrganizationName("TruFont")
    app.setOrganizationDomain("trufont.github.io")
    app.setApplicationName("TruFont")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(":app.png"))
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Install stream redirection
    app.outputWindow = OutputWindow()
    # Exception handling
    sys.excepthook = exceptionCallback

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
    if not args:
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


def exceptionCallback(etype, value, tb):
    global _showMessages
    text = "TruFont has encountered a problem and must shutdown."
    exc = traceback.format_exception(etype, value, tb)
    exc_text = "".join(exc)
    print(exc_text)

    if _showMessages:
        messageBox = QMessageBox(QMessageBox.Critical, ":(", text)
        messageBox.setStandardButtons(
            QMessageBox.Ok | QMessageBox.Close | QMessageBox.Ignore)
        messageBox.setDetailedText(exc_text)
        messageBox.setInformativeText(str(value))
        result = messageBox.exec_()
        if result == QMessageBox.Close:
            sys.exit(1)
        elif result == QMessageBox.Ignore:
            _showMessages = False

if __name__ == "__main__":
    main()
