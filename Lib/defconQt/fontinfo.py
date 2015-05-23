from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QTabWidget, QVBoxLayout, QWidget

class TabDialog(QDialog):

    def __init__(self, font, parent=None):
        super(TabDialog, self).__init__(parent)

        # TODO: figure a proper correspondence to set and fetch widgets...
        self.tabs = {
            "General": 0
        }

        self.font = font
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(GeneralTab(self.font), "General")
        self.tabWidget.addTab(NextTab(self.font), "Metrics")
#        self.tabWidget.addTab(ApplicationsTab(fileInfo), "PostScript")
#        self.tabWidget.addTab(ApplicationsTab(fileInfo), "Miscellaneous")

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Font Info")

    def accept(self):
        self.tabWidget.widget(self.tabs["General"]).writeValues(self.font)
        super(TabDialog, self).accept()

class GeneralTab(QWidget):
    def __init__(self, font, parent=None):
        super(GeneralTab, self).__init__(parent)
        mainLayout = QGridLayout(self)

        familyNameLabel = QLabel("Family name:", self)
        self.familyNameEdit = QLineEdit(font.info.familyName, self)
        styleNameLabel = QLabel("Style name:", self)
        self.styleNameEdit = QLineEdit(font.info.styleName, self)
        
        mainLayout.addWidget(familyNameLabel, 0, 0)
        mainLayout.addWidget(self.familyNameEdit, 0, 1, 1, 3)
        mainLayout.addWidget(styleNameLabel, 0, 4)
        mainLayout.addWidget(self.styleNameEdit, 0, 5)

        designerLabel = QLabel("Designer:", self)
        self.designerEdit = QLineEdit(font.info.openTypeNameDesigner, self)

        mainLayout.addWidget(designerLabel, 1, 0)
        mainLayout.addWidget(self.designerEdit, 1, 1, 1, 5)

        designerURLLabel = QLabel("Designer URL:", self)
        self.designerURLEdit = QLineEdit(font.info.openTypeNameDesignerURL, self)

        mainLayout.addWidget(designerURLLabel, 2, 0)
        mainLayout.addWidget(self.designerURLEdit, 2, 1, 1, 5)

        manufacturerLabel = QLabel("Manufacturer:", self)
        self.manufacturerEdit = QLineEdit(font.info.openTypeNameManufacturer, self)
        
        mainLayout.addWidget(manufacturerLabel, 3, 0)
        mainLayout.addWidget(self.manufacturerEdit, 3, 1, 1, 5)

        manufacturerURLLabel = QLabel("Manufacturer URL:", self)
        self.manufacturerURLEdit = QLineEdit(font.info.openTypeNameManufacturerURL, self)
        
        mainLayout.addWidget(manufacturerURLLabel, 4, 0)
        mainLayout.addWidget(self.manufacturerURLEdit, 4, 1, 1, 5)
        
        copyrightLabel = QLabel("Copyright:", self)
        self.copyrightEdit = QLineEdit(font.info.copyright, self)
        
        mainLayout.addWidget(copyrightLabel, 5, 0)
        mainLayout.addWidget(self.copyrightEdit, 5, 1, 1, 5)
        
        # TODO: give visual feedback of input data validity using QLineEdit lose focus event
        # http://snorf.net/blog/2014/08/09/using-qvalidator-in-pyqt4-to-validate-user-input/
        versionLabel = QLabel("Version:", self)
        self.versionMajorEdit = QLineEdit(str(font.info.versionMajor or ''), self)
        self.versionMajorEdit.setAlignment(Qt.AlignRight)
        self.versionMajorEdit.setValidator(QIntValidator(self))
        versionDotLabel = QLabel(".", self)
        self.versionMinorEdit = QLineEdit(str(font.info.versionMinor or ''), self)#.zfill(3))
        self.versionMinorEdit.setValidator(QIntValidator(self))
        
        mainLayout.addWidget(versionLabel, 6, 0)
        mainLayout.addWidget(self.versionMajorEdit, 6, 1)
        mainLayout.addWidget(versionDotLabel, 6, 2)
        mainLayout.addWidget(self.versionMinorEdit, 6, 3)
        
        unitsPerEmLabel = QLabel("Units per em:", self)
        self.unitsPerEmEdit = QLineEdit(str(font.info.unitsPerEm or ''), self)
        self.unitsPerEmEdit.setValidator(QIntValidator(self))
        
        mainLayout.addWidget(unitsPerEmLabel, 6, 4)
        mainLayout.addWidget(self.unitsPerEmEdit, 6, 5)
        
        licenseLabel = QLabel("License:", self)
        self.licenseEdit = QLineEdit(font.info.openTypeNameLicense, self)
        
        mainLayout.addWidget(licenseLabel, 7, 0)
        mainLayout.addWidget(self.licenseEdit, 7, 1, 1, 5)

        licenseURLLabel = QLabel("License URL:", self)
        self.licenseURLEdit = QLineEdit(font.info.openTypeNameLicenseURL, self)
        
        mainLayout.addWidget(licenseURLLabel, 8, 0)
        mainLayout.addWidget(self.licenseURLEdit, 8, 1, 1, 5)
        
        trademarkLabel = QLabel("Trademark:", self)
        self.trademarkEdit = QLineEdit(font.info.trademark, self)
        
        mainLayout.addWidget(trademarkLabel, 9, 0)
        mainLayout.addWidget(self.trademarkEdit, 9, 1, 1, 5)

        self.setLayout(mainLayout)
    
    def writeValues(self, font):
        font.info.familyName = self.familyNameEdit.text()
        font.info.styleName = self.styleNameEdit.text()
        font.info.openTypeNameDesigner = self.designerEdit.text()
        font.info.openTypeNameDesignerURL = self.designerURLEdit.text()
        font.info.openTypeNameManufacturer = self.manufacturerEdit.text()
        font.info.openTypeNameManufacturerURL = self.manufacturerURLEdit.text()
        font.info.copyright = self.copyrightEdit.text()
        font.info.versionMajor = int(self.versionMajorEdit.text())
        font.info.versionMinor = int(self.versionMinorEdit.text())
        font.info.unitsPerEm = int(self.unitsPerEmEdit.text())
        font.info.openTypeNameLicense = self.licenseEdit.text()
        font.info.openTypeNameLicenseURL = self.licenseURLEdit.text()
        font.info.trademark = self.trademarkEdit.text()

class NextTab(QWidget):
    def __init__(self, font, parent=None):
        super(NextTab, self).__init__(parent)
        mainLayout = QGridLayout()

        styleMapFamilyLabel = QLabel("Style map family name:", self)
        self.styleMapFamilyEdit = QLineEdit(font.info.styleMapFamilyName, self)
#        self.styleMapFamilyCBox = QCheckBox("Use default value", self)

        styleMapStyleLabel = QLabel("Style map style name:", self)
        self.styleMapStyleDrop = QComboBox(self)
#        items = ["None", "Regular", "Italic", "Bold", "Bold Italic"]
        styleMapStyle = {
            "None": 0,
            "Regular": 1,
            "Italic": 2,
            "Bold": 3,
            "Bold Italic": 4
        }
        for name,index in styleMapStyle.items():
            self.styleMapStyleDrop.insertItem(index, name)
        sn = font.info.styleMapStyleName
        # TODO: index to set is statically known, should eventually get rid of dict overhead if any?
        if sn == "regular": self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["Regular"])
        elif sn == "regular italic": self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["Italic"])
        elif sn == "bold": self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["Bold"])
        elif sn == "bold italic": self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["Bold Italic"])
        else: self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["None"])
#        self.styleMapStyleCBox = QCheckBox("Use default value")

        mainLayout.addWidget(styleMapFamilyLabel, 0, 0)
        mainLayout.addWidget(self.styleMapFamilyEdit, 0, 1, 1, 3)
        mainLayout.addWidget(styleMapStyleLabel, 0, 4)
        mainLayout.addWidget(self.styleMapStyleDrop, 0, 5)

        ascenderLabel = QLabel("Ascender:", self)
        self.ascenderEdit = QLineEdit(str(font.info.ascender or ''), self)
        self.ascenderEdit.setValidator(QIntValidator(self))

        descenderLabel = QLabel("Descender:", self)
        self.descenderEdit = QLineEdit(str(font.info.descender or ''), self)
        self.descenderEdit.setValidator(QIntValidator(self))

        italicAngleLabel = QLabel("Italic angle:", self)
        self.italicAngleEdit = QLineEdit(str(font.info.italicAngle or ''), self)
        self.italicAngleEdit.setValidator(QDoubleValidator(self))
        
        mainLayout.addWidget(ascenderLabel, 1, 0)
        mainLayout.addWidget(self.ascenderEdit, 1, 1)
        mainLayout.addWidget(descenderLabel, 1, 2)
        mainLayout.addWidget(self.descenderEdit, 1, 3)
        mainLayout.addWidget(italicAngleLabel, 1, 4)
        mainLayout.addWidget(self.italicAngleEdit, 1, 5)

        xHeightLabel = QLabel("x-height:", self)
        self.xHeightEdit = QLineEdit(str(font.info.xHeight or ''), self)
        self.xHeightEdit.setValidator(QIntValidator(self))

        capHeightLabel = QLabel("Cap height:", self)
        self.capHeightEdit = QLineEdit(str(font.info.capHeight or ''), self)
        self.capHeightEdit.setValidator(QIntValidator(self))
        
        mainLayout.addWidget(xHeightLabel, 2, 0)
        mainLayout.addWidget(self.xHeightEdit, 2, 1)
        mainLayout.addWidget(capHeightLabel, 2, 2)
        mainLayout.addWidget(self.capHeightEdit, 2, 3)
        
        self.setLayout(mainLayout)
        
    def writeValues(self, font):
        font.info.styleMapFamilyName = self.styleMapFamilyEdit.text()
        sn = self.styleMapStyleDrop.currentIndex()
        if sn == 1: font.info.styleMapStyleName = "regular"
        elif sn == 2: font.info.styleMapStyleName = "italic"
        elif sn == 3: font.info.styleMapStyleName = "bold"
        elif sn == 4: font.info.styleMapStyleName = "bold italic"
        else: font.info.styleMapStyleName = None