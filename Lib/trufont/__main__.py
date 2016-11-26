from defconQt import representationFactories as baseRepresentationFactories
from trufont import __version__, representationFactories
from trufont.objects import settings
from trufont.objects.application import Application
from trufont.objects.extension import TExtension
from trufont.resources import icons_db  # noqa
from trufont.tools import errorReports, platformSpecific
from trufont.windows.outputWindow import OutputWindow
from PyQt5.QtCore import (
    Qt, QCommandLineParser, QTranslator, QLocale, QLibraryInfo)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
import os
import sys


def main():
    global app
    # register representation factories
    baseRepresentationFactories.registerAllFactories()
    representationFactories.registerAllFactories()
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # initialize the app
    app = Application(sys.argv)
    app.setOrganizationName("TruFont")
    app.setOrganizationDomain("trufont.github.io")
    app.setApplicationName("TruFont")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(":app.png"))
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setStyleSheet(platformSpecific.appStyleSheet())

    # Install stream redirection
    app.outputWindow = OutputWindow()
    # Exception handling
    sys.excepthook = errorReports.exceptionCallback

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
    # load menu
    if platformSpecific.useGlobalMenuBar():
        app.fetchMenuBar()
        app.setQuitOnLastWindowClosed(False)
    # bootstrap extensions
    folder = app.getExtensionsDirectory()
    for file in os.listdir(folder):
        if not file.rstrip("\\/ ").endswith(".tfExt"):
            continue
        path = os.path.join(folder, file)
        try:
            extension = TExtension(path)
            if extension.launchAtStartup:
                extension.run()
        except Exception as e:
            msg = QApplication.translate(
                "Extensions", "The extension at {0} could not be run.".format(
                    path))
            errorReports.showWarningException(e, msg)
            continue
        app.registerExtension(extension)
    # process files
    args = parser.positionalArguments()
    if not args:
        # maybe load recent file
        loadRecentFile = settings.loadRecentFile()
        if loadRecentFile:
            recentFiles = settings.recentFiles()
            if len(recentFiles) and os.path.exists(recentFiles[0]):
                app.openFile(recentFiles[0])
    else:
        for fontPath in args:
            app.openFile(fontPath)
    # if we did not open a font, spawn new font or go headless
    if not app.allFonts():
        if platformSpecific.shouldSpawnDocument():
            app.newFile()
        else:
            # HACK: on OSX we may want to trigger native QMenuBar display
            # without opening any window. Since Qt infers new menu bar on
            # focus change, fire the signal.
            app.focusWindowChanged.emit(None)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
