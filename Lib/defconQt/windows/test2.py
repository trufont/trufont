from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from progressWindow import *

if __name__ == '__main__':
    import sys
 
    app = QApplication(sys.argv)
 
    screen = ProgressWindow(text="Hello World!", maximum=0, parentWindow=app)
#    screen.show()
 
    sys.exit(app.exec_())