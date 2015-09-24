from defconQt.objects.defcon import TFont
from defconQt.fontView import MainWindow
import sys
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

if len(sys.argv) < 2:
    share_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'share')
    ufoFile = os.path.join(share_dir, 'fonts', 'subsets', 'Merriweather-Bold-Subset-nop.ufo')
    print ('Usage: %s <input.ufo>' % sys.argv[0])
    print ('Loading default sample font: "%s"' % ufoFile)
else:
    ufoFile = sys.argv[1]
    print('Loading font file: "%s"' % ufoFile)

#from pycallgraph import PyCallGraph
#from pycallgraph.output import GraphvizOutput
from defconQt import representationFactories
representationFactories.registerAllFactories()
#with PyCallGraph(output=GraphvizOutput()):
app = QApplication(sys.argv)
# TODO: http://stackoverflow.com/a/21330349/2037879
app.setWindowIcon(QIcon("defconQt/resources/icon.png"))
window = MainWindow(TFont(os.path.abspath(ufoFile)))
window.show()
sys.exit(app.exec_())
