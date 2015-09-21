from defconQt.objects.defcon import TFont
from defconQt.fontView import MainWindow
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

if len(sys.argv) < 2:
    ufoFile = "C:\\CharterNova-Regular.ufo"
#    print('Usage: %s INPUTFILE' % sys.argv[0])
#    sys.exit(1)
else:
     ufoFile = sys.argv[1]

#from pycallgraph import PyCallGraph
#from pycallgraph.output import GraphvizOutput
from defconQt import representationFactories
representationFactories.registerAllFactories()
#with PyCallGraph(output=GraphvizOutput()):
app = QApplication(sys.argv)
# TODO: http://stackoverflow.com/a/21330349/2037879
app.setWindowIcon(QIcon("defconQt/resources/icon.png"))
window = MainWindow(TFont(ufoFile))
window.show()
sys.exit(app.exec_())
