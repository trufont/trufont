from PyQt5.QtCore import QDate, QDateTime, QTime, Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QTabWidget, QVBoxLayout, QWidget

class TabDialog(QDialog):

    def __init__(self, font, parent=None):
        super(TabDialog, self).__init__(parent)

        # TODO: figure a proper correspondence to set and fetch widgets...
        self.tabs = {
            "General": 0,
            "Metrics": 1,
            "OpenType": 2
        }

        self.font = font
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(GeneralTab(self.font), "General")
        self.tabWidget.addTab(MetricsTab(self.font), "Metrics")
#        self.tabWidget.addTab(ApplicationsTab(fileInfo), "OpenType")
#        self.tabWidget.addTab(ApplicationsTab(fileInfo), "PostScript")
#        self.tabWidget.addTab(ApplicationsTab(fileInfo), "Miscellaneous")

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("%s%s%s%s" % ("Font Info – ", self.font.info.familyName, " ", self.font.info.styleName))

    def accept(self):
        self.tabWidget.widget(self.tabs["General"]).writeValues(self.font)
        self.tabWidget.widget(self.tabs["Metrics"]).writeValues(self.font)
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
        versionMajor = str(font.info.versionMajor) if font.info.versionMajor is not None else ''
        self.versionMajorEdit = QLineEdit(versionMajor, self)
        self.versionMajorEdit.setAlignment(Qt.AlignRight)
        self.versionMajorEdit.setValidator(QIntValidator(self))
        versionDotLabel = QLabel(".", self)
        versionMinor = str(font.info.versionMinor) if font.info.versionMinor is not None else ''
        self.versionMinorEdit = QLineEdit(versionMinor, self)
        self.versionMinorEdit.setValidator(QIntValidator(self))
        
        mainLayout.addWidget(versionLabel, 6, 0)
        mainLayout.addWidget(self.versionMajorEdit, 6, 1)
        mainLayout.addWidget(versionDotLabel, 6, 2)
        mainLayout.addWidget(self.versionMinorEdit, 6, 3)

        dateCreatedLabel = QLabel("Date created:", self)
        dateTime = QDateTime()
        #dateTime.fromString(font.info.openTypeHeadCreated, "yyyy/MM/dd hh:mm:ss") # XXX: why does this not work?
        dateCreated = font.info.openTypeHeadCreated
        if dateCreated:
            parse = dateCreated.split(" ")
            if len(parse) == 2:
                date = parse[0].split("/")
                date = QDate(*(int(val) for val in date))
                dateTime.setDate(date)
                time = parse[1].split(":")
                time = QTime(*(int(val) for val in time))
                dateTime.setTime(time)
        if not dateCreated:
            cur = QDateTime.currentDateTime()
            dateTime.setDate(cur.date())
            dateTime.setTime(cur.time())
        self.dateCreatedEdit = QDateTimeEdit(dateTime, self)
        
        mainLayout.addWidget(dateCreatedLabel, 6, 4)
        mainLayout.addWidget(self.dateCreatedEdit, 6, 5)
        
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
        versionMajor = self.versionMajorEdit.text()
        font.info.versionMajor = int(versionMajor) if versionMajor else None
        versionMinor = self.versionMinorEdit.text()
        font.info.versionMinor = int(versionMinor) if versionMinor else None
        font.info.openTypeHeadCreated = self.dateCreatedEdit.dateTime().toString("yyyy/MM/dd hh:mm:ss")
        font.info.openTypeNameLicense = self.licenseEdit.text()
        font.info.openTypeNameLicenseURL = self.licenseURLEdit.text()
        font.info.trademark = self.trademarkEdit.text()

class MetricsTab(QWidget):
    def __init__(self, font, parent=None):
        super(MetricsTab, self).__init__(parent)
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
        ascender = str(font.info.ascender) if font.info.ascender is not None else ''
        self.ascenderEdit = QLineEdit(ascender, self)
        self.ascenderEdit.setValidator(QIntValidator(self))

        descenderLabel = QLabel("Descender:", self)
        descender = str(font.info.descender) if font.info.descender is not None else ''
        self.descenderEdit = QLineEdit(descender, self)
        self.descenderEdit.setValidator(QIntValidator(self))
        
        unitsPerEmLabel = QLabel("Units per em:", self)
        unitsPerEm = str(font.info.unitsPerEm) if font.info.unitsPerEm is not None else ''
        self.unitsPerEmEdit = QLineEdit(unitsPerEm, self)
        self.unitsPerEmEdit.setValidator(QIntValidator(self))
        
        mainLayout.addWidget(ascenderLabel, 1, 0)
        mainLayout.addWidget(self.ascenderEdit, 1, 1)
        mainLayout.addWidget(descenderLabel, 1, 2)
        mainLayout.addWidget(self.descenderEdit, 1, 3)
        mainLayout.addWidget(unitsPerEmLabel, 1, 4)
        mainLayout.addWidget(self.unitsPerEmEdit, 1, 5)

        xHeightLabel = QLabel("x-height:", self)
        xHeight = str(font.info.xHeight) if font.info.xHeight is not None else ''
        self.xHeightEdit = QLineEdit(xHeight, self)
        self.xHeightEdit.setValidator(QIntValidator(self))

        capHeightLabel = QLabel("Cap height:", self)
        capHeight = str(font.info.capHeight) if font.info.capHeight is not None else ''
        self.capHeightEdit = QLineEdit(capHeight, self)
        self.capHeightEdit.setValidator(QIntValidator(self))

        italicAngleLabel = QLabel("Italic angle:", self)
        italicAngle = str(font.info.italicAngle) if font.info.italicAngle is not None else ''
        self.italicAngleEdit = QLineEdit(italicAngle, self)
        self.italicAngleEdit.setValidator(QDoubleValidator(self))
        
        mainLayout.addWidget(xHeightLabel, 2, 0)
        mainLayout.addWidget(self.xHeightEdit, 2, 1)
        mainLayout.addWidget(capHeightLabel, 2, 2)
        mainLayout.addWidget(self.capHeightEdit, 2, 3)
        mainLayout.addWidget(italicAngleLabel, 2, 4)
        mainLayout.addWidget(self.italicAngleEdit, 2, 5)
        
        self.setLayout(mainLayout)
        
    def writeValues(self, font):
        font.info.styleMapFamilyName = self.styleMapFamilyEdit.text()
        sn = self.styleMapStyleDrop.currentIndex()
        if sn == 1: font.info.styleMapStyleName = "regular"
        elif sn == 2: font.info.styleMapStyleName = "italic"
        elif sn == 3: font.info.styleMapStyleName = "bold"
        elif sn == 4: font.info.styleMapStyleName = "bold italic"
        else: font.info.styleMapStyleName = None
        ascender = self.ascenderEdit.text()
        font.info.ascender = int(ascender) if ascender else None
        descender = self.descenderEdit.text()
        font.info.descender = int(descender) if descender else None
        unitsPerEm = self.unitsPerEmEdit.text()
        font.info.unitsPerEm = int(unitsPerEm) if unitsPerEm else None
        xHeight = self.xHeightEdit.text()
        font.info.xHeight = int(xHeight) if xHeight else None
        capHeight = self.capHeightEdit.text()
        font.info.capHeight = int(capHeight) if capHeight else None
        italicAngle = self.italicAngleEdit.text()
        font.info.italicAngle = float(italicAngle) if italicAngle else None
