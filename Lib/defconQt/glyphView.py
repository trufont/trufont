class MainSpaceWindow(QWidget):
    def __init__(self):
        self.scene = QGraphicsScene()
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.scene)