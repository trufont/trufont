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

#        fileInfo = QFileInfo(fileName)
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
        mainLayout = QGridLayout()

        familyNameLabel = QLabel("Family name:")
        self.familyNameEdit = QLineEdit(font.info.familyName)
        styleNameLabel = QLabel("Style name:")
        self.styleNameEdit = QLineEdit(font.info.styleName)
        
        mainLayout.addWidget(familyNameLabel, 0, 0)
        mainLayout.addWidget(self.familyNameEdit, 0, 1, 1, 3)
        mainLayout.addWidget(styleNameLabel, 0, 4)
        mainLayout.addWidget(self.styleNameEdit, 0, 5)

        designerLabel = QLabel("Designer:")
        self.designerEdit = QLineEdit(font.info.openTypeNameDesigner)

        mainLayout.addWidget(designerLabel, 1, 0)
        mainLayout.addWidget(self.designerEdit, 1, 1, 1, 5)

        designerURLLabel = QLabel("Designer URL:")
        self.designerURLEdit = QLineEdit(font.info.openTypeNameDesignerURL)

        mainLayout.addWidget(designerURLLabel, 2, 0)
        mainLayout.addWidget(self.designerURLEdit, 2, 1, 1, 5)

        manufacturerLabel = QLabel("Manufacturer:")
        self.manufacturerEdit = QLineEdit(font.info.openTypeNameManufacturer)
        
        mainLayout.addWidget(manufacturerLabel, 3, 0)
        mainLayout.addWidget(self.manufacturerEdit, 3, 1, 1, 5)

        manufacturerURLLabel = QLabel("Manufacturer URL:")
        self.manufacturerURLEdit = QLineEdit(font.info.openTypeNameManufacturerURL)
        
        mainLayout.addWidget(manufacturerURLLabel, 4, 0)
        mainLayout.addWidget(self.manufacturerURLEdit, 4, 1, 1, 5)
        
        copyrightLabel = QLabel("Copyright:")
        self.copyrightEdit = QLineEdit(font.info.copyright)
        
        mainLayout.addWidget(copyrightLabel, 5, 0)
        mainLayout.addWidget(self.copyrightEdit, 5, 1, 1, 5)
        
        # TODO: give visual feedback of input data validity using QLineEdit lose focus event
        # http://snorf.net/blog/2014/08/09/using-qvalidator-in-pyqt4-to-validate-user-input/
        versionLabel = QLabel("Version:")
        self.versionMajorEdit = QLineEdit(str(font.info.versionMajor))
        self.versionMajorEdit.setAlignment(Qt.AlignRight)
        self.versionMajorEdit.setValidator(QIntValidator())
        versionDotLabel = QLabel(".")
        self.versionMinorEdit = QLineEdit(str(font.info.versionMinor).zfill(3))
        self.versionMinorEdit.setValidator(QIntValidator())
        
        mainLayout.addWidget(versionLabel, 6, 0)
        mainLayout.addWidget(self.versionMajorEdit, 6, 1)
        mainLayout.addWidget(versionDotLabel, 6, 2)
        mainLayout.addWidget(self.versionMinorEdit, 6, 3)
        
        unitsPerEmLabel = QLabel("Units per em:")
        self.unitsPerEmEdit = QLineEdit(str(font.info.unitsPerEm))
        self.unitsPerEmEdit.setValidator(QIntValidator())
        
        mainLayout.addWidget(unitsPerEmLabel, 6, 4)
        mainLayout.addWidget(self.unitsPerEmEdit, 6, 5)
        
        licenseLabel = QLabel("License:")
        self.licenseEdit = QLineEdit(font.info.openTypeNameLicense)
        
        mainLayout.addWidget(licenseLabel, 7, 0)
        mainLayout.addWidget(self.licenseEdit, 7, 1, 1, 5)

        licenseURLLabel = QLabel("License URL:")
        self.licenseURLEdit = QLineEdit(font.info.openTypeNameLicenseURL)
        
        mainLayout.addWidget(licenseURLLabel, 8, 0)
        mainLayout.addWidget(self.licenseURLEdit, 8, 1, 1, 5)
        
        trademarkLabel = QLabel("Trademark:")
        self.trademarkEdit = QLineEdit(font.info.trademark)
        
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
        """
        font.info.styleMapFamilyName = self.styleMapFamilyEdit.text()
        sn = self.styleMapStyleDrop.currentIndex()
        if sn == 1: font.info.styleMapStyleName = "regular"
        elif sn == 2: font.info.styleMapStyleName = "italic"
        elif sn == 3: font.info.styleMapStyleName = "bold"
        elif sn == 4: font.info.styleMapStyleName = "bold italic"
        else: font.info.styleMapStyleName = None
        """

class NextTab(QWidget):
    def __init__(self, font, parent=None):
        super(NextTab, self).__init__(parent)
        mainLayout = QGridLayout()

        styleMapFamilyLabel = QLabel("Style map family name:")
        self.styleMapFamilyEdit = QLineEdit(font.info.styleMapFamilyName)
#        self.styleMapFamilyCBox = QCheckBox("Use default value")

        styleMapStyleLabel = QLabel("Style map style name:")
        self.styleMapStyleDrop = QComboBox()
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

        ascenderLabel = QLabel("Ascender:")
        self.ascenderEdit = QLineEdit(str(font.info.ascender))
        self.ascenderEdit.setValidator(QIntValidator())

        descenderLabel = QLabel("Descender:")
        self.descenderEdit = QLineEdit(str(font.info.descender))
        self.descenderEdit.setValidator(QIntValidator())

        italicAngleLabel = QLabel("Italic angle:")
        self.italicAngleEdit = QLineEdit(str(font.info.italicAngle))
        self.italicAngleEdit.setValidator(QDoubleValidator())
        
        mainLayout.addWidget(ascenderLabel, 1, 0)
        mainLayout.addWidget(self.ascenderEdit, 1, 1)
        mainLayout.addWidget(descenderLabel, 1, 2)
        mainLayout.addWidget(self.descenderEdit, 1, 3)
        mainLayout.addWidget(italicAngleLabel, 1, 4)
        mainLayout.addWidget(self.italicAngleEdit, 1, 5)

        xHeightLabel = QLabel("x-height:")
        self.xHeightEdit = QLineEdit(str(font.info.xHeight))
        self.xHeightEdit.setValidator(QIntValidator())

        capHeightLabel = QLabel("Cap height:")
        self.capHeightEdit = QLineEdit(str(font.info.capHeight))
        self.capHeightEdit.setValidator(QIntValidator())
        
        mainLayout.addWidget(xHeightLabel, 2, 0)
        mainLayout.addWidget(self.xHeightEdit, 2, 1)
        mainLayout.addWidget(capHeightLabel, 2, 2)
        mainLayout.addWidget(self.capHeightEdit, 2, 3)
        
        self.setLayout(mainLayout)