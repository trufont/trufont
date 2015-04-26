#import vanilla
try:
    from defconQt.windows.baseWindow import BaseWindowController
except:
    from baseWindow import BaseWindowController
from PyQt5.QtWidgets import QProgressDialog

class ProgressWindow(BaseWindowController):

    def __init__(self, text="", maximum=0, parentWindow=None):
        self.w = parentWindow
        if parentWindow is None:
            raise NotImplementedError
#            self.w = vanilla.Window((250, 60), closable=False, miniaturizable=False, textured=False)
#        else:
#            self.w = vanilla.Sheet((250, 60), parentWindow)
        # have it uncancelable for now at least
        #self.w.progress = QProgressDialog(cancelButtonText="0", parent=parentWindow, labelText=text, maximum=maximum)
        self.w.progress = QProgressDialog(parent=parentWindow, labelText=text, maximum=maximum)
#        self.w.progress.setWindowModality(Qt::WindowModal)
#        self.w.progress = vanilla.ProgressBar((15, 15, -15, 12), maxValue=tickCount, isIndeterminate=isIndeterminate, sizeStyle="small")
#        self.w.text = vanilla.TextBox((15, 32, -15, 14), text, sizeStyle="small")
#        self.w.progress.start()
#        self.w.center()
#        self.setUpBaseWindowBehavior()
#        self.w.open()
        self.w.progress.open()

    def close(self):
        self.progress.cancel()
#        self.w.close()

    def update(self, text=None):
#        self.w.progress.increment()
        cur = self.progress.value()
        self.progress.setValue(cur+1)
        if text is not None:
            self.setLabelText(text)
#        self.w.text._nsObject.display()

    def setTickCount(self, value=0):
#        bar = self.w.progress.getNSProgressIndicator()
#        if value is None:
#            bar.setIndeterminate_(True)
#            self.w.progress.start()
#        else:
#            bar.setIndeterminate_(False)
#            bar.setDoubleValue_(0)
#            bar.setMaxValue_(value)
        self.progress.setRange(0, value)