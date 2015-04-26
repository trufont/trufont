from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from progressWindow import *

if __name__ == '__main__':
    import sys
 
    app = QApplication(sys.argv)
 
    screen = BaseWindowController()
    screen.w = None
    screen.startProgress("Hello World!", 5)
#    screen.show()
 
    sys.exit(app.exec_())