from defconQt.objects.defcon import TFont
from defconQt import representationFactories
from defconQt import icons_db  # noqa
from defconQt.fontView import Application, MainWindow
import sys
import os
from PyQt5.QtGui import QIcon


def main():

    if len(sys.argv) > 1:
        font = TFont(os.path.abspath(sys.argv[1]))
    else:
        font = None

    representationFactories.registerAllFactories()
    app = Application(sys.argv)
    # TODO: http://stackoverflow.com/a/21330349/2037879
    app.setOrganizationName("A. Tétar & Co.")
    app.setOrganizationDomain("trufont.github.io")
    app.setApplicationName("TruFont")
    app.setWindowIcon(QIcon(":/resources/app.png"))
    window = MainWindow(font)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
