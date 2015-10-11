from defconQt.objects.defcon import TFont
from defconQt import representationFactories
from defconQt.fontView import Application, MainWindow
import sys
import os
from PyQt5.QtGui import QIcon

if len(sys.argv) > 1:
    font = TFont(os.path.abspath(sys.argv[1]))
else:
    font = None

#from pycallgraph import PyCallGraph
#from pycallgraph.output import GraphvizOutput
representationFactories.registerAllFactories()
#with PyCallGraph(output=GraphvizOutput()):
app = Application(sys.argv)
# TODO: http://stackoverflow.com/a/21330349/2037879
app.setOrganizationName("A. Tétar & Co.")
app.setApplicationName("TruFont")
app.setWindowIcon(QIcon("defconQt/resources/app.png"))
window = MainWindow(font)
window.show()
sys.exit(app.exec_())
