from defconQt import representationFactories
from defconQt import icons_db  # noqa
from defconQt.fontView import Application, MainWindow
from defconQt.objects.defcon import TFont
import sys
import os
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QIcon


def main():

    if len(sys.argv) > 1:
        font = TFont(os.path.abspath(sys.argv[1]))
    else:
        font = None

    representationFactories.registerAllFactories()
    app = Application(sys.argv)
    # TODO: http://stackoverflow.com/a/21330349/2037879
    app.setOrganizationName("TruFont")
    app.setOrganizationDomain("trufont.github.io")
    app.setApplicationName("TruFont")
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
    window = MainWindow(font)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
