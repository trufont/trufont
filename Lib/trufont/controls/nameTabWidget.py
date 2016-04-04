from PyQt5.QtWidgets import QTabWidget


class NameTabWidget(QTabWidget):

    def addNamedTab(self, tab):
        self.addTab(tab, tab.name)
