from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFrame, QLabel, QLineEdit, QScrollArea, QTabWidget, QVBoxLayout, QWidget

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
#        tabWidget.addTab(PermissionsTab(fileInfo), "OpenType")
#        tabWidget.addTab(ApplicationsTab(fileInfo), "PostScript")
#        tabWidget.addTab(ApplicationsTab(fileInfo), "Miscellaneous")

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Font Info")

    def accept(self):
        self.font.info.familyName = self.tabWidget.widget(self.tabs["General"]).fileNameEdit.text()
        self.font.info.styleName = self.tabWidget.widget(self.tabs["General"]).styleNameEdit.text()
        self.font.info.styleMapFamilyName = self.tabWidget.widget(self.tabs["General"]).styleMapFamilyEdit.text()
        sn = self.tabWidget.widget(self.tabs["General"]).styleMapStyleDrop.currentIndex()
        print(sn)
        if sn == 1: self.font.info.styleMapStyleName = "regular"
        elif sn == 2: self.font.info.styleMapStyleName = "italic"
        elif sn == 3: self.font.info.styleMapStyleName = "bold"
        elif sn == 4: self.font.info.styleMapStyleName = "bold italic"
        else: self.font.info.styleMapStyleName = None
        self.font.info.versionMajor = int(self.tabWidget.widget(self.tabs["General"]).versionMajorEdit.text())
        self.font.info.versionMinor = int(self.tabWidget.widget(self.tabs["General"]).versionMinorEdit.text())
        super(TabDialog, self).accept()

class GeneralTab(QWidget):
    def __init__(self, font, parent=None):
        super(GeneralTab, self).__init__(parent)

        identLabel = QLabel("Identification")
        identLine = QFrame()
        identLine.setFrameShape(QFrame.HLine)

        fileNameLabel = QLabel("Family name:")
        self.fileNameEdit = QLineEdit(font.info.familyName)

        styleNameLabel = QLabel("Style name:")
        self.styleNameEdit = QLineEdit(font.info.styleName)

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

        # TODO: give visual feedback of input data validity using QLineEdit lose focus event
        # http://snorf.net/blog/2014/08/09/using-qvalidator-in-pyqt4-to-validate-user-input/
        versionLabel = QLabel("Version:")
        self.versionMajorEdit = QLineEdit(str(font.info.versionMajor))
        self.versionMajorEdit.setValidator(QIntValidator())
        self.versionMinorEdit = QLineEdit(str(font.info.versionMinor))
        self.versionMinorEdit.setValidator(QIntValidator())

        dimensionsLabel = QLabel("Dimensions")
        dimensionsLine = QFrame()
        dimensionsLine.setFrameShape(QFrame.HLine)

        unitsPerEmLabel = QLabel("Units per em:")
        self.unitsPerEmEdit = QLineEdit(str(font.info.unitsPerEm))
        self.unitsPerEmEdit.setValidator(QIntValidator())

        ascenderLabel = QLabel("Ascender:")
        self.ascenderEdit = QLineEdit(str(font.info.ascender))
        self.ascenderEdit.setValidator(QIntValidator())

        descenderLabel = QLabel("Descender:")
        self.descenderEdit = QLineEdit(str(font.info.descender))
        self.descenderEdit.setValidator(QIntValidator())

        xHeightLabel = QLabel("x-height:")
        self.xHeightEdit = QLineEdit(str(font.info.xHeight))
        self.xHeightEdit.setValidator(QIntValidator())

        capHeightLabel = QLabel("Cap height:")
        self.capHeightEdit = QLineEdit(str(font.info.capHeight))
        self.capHeightEdit.setValidator(QIntValidator())

        italicAngleLabel = QLabel("Italic angle:")
        self.italicAngleEdit = QLineEdit(str(font.info.italicAngle))
        self.italicAngleEdit.setValidator(QDoubleValidator())

        legalLabel = QLabel("Legal")
        legalLine = QFrame()
        legalLine.setFrameShape(QFrame.HLine)

        copyrightLabel = QLabel("Copyright:")
        self.copyrightEdit = QLineEdit(font.info.copyright)

        trademarkLabel = QLabel("Trademark:")
        self.trademarkEdit = QLineEdit(font.info.trademark)

        licenseLabel = QLabel("License:")
        self.licenseEdit = QLineEdit(font.info.openTypeNameLicense)

        licenseURLLabel = QLabel("License URL:")
        self.licenseURLEdit = QLineEdit(font.info.openTypeNameLicenseURL)

        partiesLabel = QLabel("Parties")
        partiesLine = QFrame()
        partiesLine.setFrameShape(QFrame.HLine)

        designerLabel = QLabel("Designer:")
        self.designerEdit = QLineEdit(font.info.openTypeNameDesigner)

        designerURLLabel = QLabel("Designer URL:")
        self.designerURLEdit = QLineEdit(font.info.openTypeNameDesignerURL)

        manufacturerLabel = QLabel("Manufacturer:")
        self.manufacturerEdit = QLineEdit(font.info.openTypeNameManufacturer)

        manufacturerURLLabel = QLabel("Manufacturer URL:")
        self.manufacturerURLEdit = QLineEdit(font.info.openTypeNameManufacturerURL)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(identLabel)
        mainLayout.addWidget(identLine)
        mainLayout.addWidget(fileNameLabel)
        mainLayout.addWidget(self.fileNameEdit)
        mainLayout.addWidget(styleNameLabel)
        mainLayout.addWidget(self.styleNameEdit)
        mainLayout.addWidget(styleMapFamilyLabel)
        mainLayout.addWidget(self.styleMapFamilyEdit)
        mainLayout.addWidget(styleMapStyleLabel)
        mainLayout.addWidget(self.styleMapStyleDrop)
        mainLayout.addWidget(versionLabel)
        mainLayout.addWidget(self.versionMajorEdit)
        mainLayout.addWidget(self.versionMinorEdit)

        mainLayout.addWidget(dimensionsLabel)
        mainLayout.addWidget(dimensionsLine)
        mainLayout.addWidget(unitsPerEmLabel)
        mainLayout.addWidget(self.unitsPerEmEdit)
        mainLayout.addWidget(ascenderLabel)
        mainLayout.addWidget(self.ascenderEdit)
        mainLayout.addWidget(descenderLabel)
        mainLayout.addWidget(self.descenderEdit)
        mainLayout.addWidget(xHeightLabel)
        mainLayout.addWidget(self.xHeightEdit)
        mainLayout.addWidget(capHeightLabel)
        mainLayout.addWidget(self.capHeightEdit)
        mainLayout.addWidget(italicAngleLabel)
        mainLayout.addWidget(self.italicAngleEdit)

        mainLayout.addWidget(legalLabel)
        mainLayout.addWidget(legalLine)
        mainLayout.addWidget(copyrightLabel)
        mainLayout.addWidget(self.copyrightEdit)
        mainLayout.addWidget(trademarkLabel)
        mainLayout.addWidget(self.trademarkEdit)
        mainLayout.addWidget(licenseLabel)
        mainLayout.addWidget(self.licenseEdit)
        mainLayout.addWidget(licenseURLLabel)
        mainLayout.addWidget(self.licenseURLEdit)

        mainLayout.addWidget(partiesLabel)
        mainLayout.addWidget(partiesLine)
        mainLayout.addWidget(designerLabel)
        mainLayout.addWidget(self.designerEdit)
        mainLayout.addWidget(designerURLLabel)
        mainLayout.addWidget(self.designerURLEdit)
        mainLayout.addWidget(manufacturerLabel)
        mainLayout.addWidget(self.manufacturerEdit)
        mainLayout.addWidget(manufacturerURLLabel)
        mainLayout.addWidget(self.manufacturerURLEdit)
        mainLayout.addStretch(1)

        # http://nealbuerger.com/2013/11/pyside-qvboxlayout-with-qscrollarea/
        # Why so many layers of indirection? It might be possible to do this
        # in a simpler way...
        widget = QWidget()
        widget.setLayout(mainLayout)
        scrollArea = QScrollArea()
        scrollArea.setWidget(widget)
        scrollArea.setMinimumSize(170, 200)
        vLayout = QVBoxLayout()
        vLayout.addWidget(scrollArea)

        self.setLayout(vLayout)