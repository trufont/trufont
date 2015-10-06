from PyQt5.QtCore import *#QDate, QDateTime, QTime, Qt
from PyQt5.QtGui import *#QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import *#QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QTabWidget, QVBoxLayout, QWidget

class InfoTabWidget(QTabWidget):
    def addNamedTab(self, tab):
        self.addTab(tab, tab.name)

class TabDialog(QDialog):
    def __init__(self, font, parent=None):
        super(TabDialog, self).__init__(parent)
        self.font = font

        self.tabWidget = InfoTabWidget(self)
        self.tabWidget.addNamedTab(GeneralTab(self.font))
        self.tabWidget.addNamedTab(MetricsTab(self.font))
        self.tabWidget.addNamedTab(OpenTypeTab(self.font))
        self.tabWidget.addNamedTab(PostScriptTab(self.font))

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Font Info – %s %s" % (self.font.info.familyName, self.font.info.styleName))

    def accept(self):
        for i in range(self.tabWidget.count()):
            self.tabWidget.widget(i).writeValues(self.font)
        super(TabDialog, self).accept()

class GeneralTab(QWidget):
    name = "General"

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
        validator = QIntValidator(self)
        validator.setBottom(0)
        self.versionMinorEdit.setValidator(validator)

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
        else:
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
        familyName = self.familyNameEdit.text()
        font.info.familyName = familyName if familyName != '' else None
        styleName = self.styleNameEdit.text()
        font.info.styleName = styleName if styleName != '' else None
        designer = self.designerEdit.text()
        font.info.openTypeNameDesigner = designer if designer != '' else None
        designerURL = self.designerURLEdit.text()
        font.info.openTypeNameDesignerURL = designerURL if designerURL != '' else None
        manufacturer = self.manufacturerEdit.text()
        font.info.openTypeNameManufacturer = manufacturer if manufacturer != '' else None
        manufacturerURL = self.manufacturerURLEdit.text()
        font.info.openTypeNameManufacturerURL = manufacturerURL if manufacturerURL != '' else None
        copyright = self.copyrightEdit.text()
        font.info.copyright = copyright if copyright != '' else None
        versionMajor = self.versionMajorEdit.text()
        font.info.versionMajor = int(versionMajor) if versionMajor else None
        versionMinor = self.versionMinorEdit.text()
        font.info.versionMinor = int(versionMinor) if versionMinor else None
        font.info.openTypeHeadCreated = self.dateCreatedEdit.dateTime().toString("yyyy/MM/dd hh:mm:ss")
        license = self.licenseEdit.text()
        font.info.openTypeNameLicense = license if license != '' else None
        licenseURL = self.licenseURLEdit.text()
        font.info.openTypeNameLicenseURL = licenseURL if licenseURL != '' else None
        trademark = self.trademarkEdit.text()
        font.info.trademark = trademark if trademark != '' else None

class MetricsTab(QWidget):
    name = "Metrics"

    def __init__(self, font, parent=None):
        super(MetricsTab, self).__init__(parent)
        mainLayout = QGridLayout()

        styleMapFamilyLabel = QLabel("Style map family name:", self)
        self.styleMapFamilyEdit = QLineEdit(font.info.styleMapFamilyName, self)

        styleMapStyleLabel = QLabel("Style map style name:", self)
        self.styleMapStyleDrop = QComboBox(self)
        items = ["None", "Regular", "Italic", "Bold", "Bold Italic"]
        self.styleMapStyleDrop.insertItems(0, items)
        sn = font.info.styleMapStyleName
        if sn == "regular": self.styleMapStyleDrop.setCurrentIndex(1)
        elif sn == "regular italic": self.styleMapStyleDrop.setCurrentIndex(2)
        elif sn == "bold": self.styleMapStyleDrop.setCurrentIndex(3)
        elif sn == "bold italic": self.styleMapStyleDrop.setCurrentIndex(4)
        else: self.styleMapStyleDrop.setCurrentIndex(0)

        mainLayout.addWidget(styleMapFamilyLabel, 0, 0)
        mainLayout.addWidget(self.styleMapFamilyEdit, 0, 1, 1, 3)
        mainLayout.addWidget(styleMapStyleLabel, 0, 4)
        mainLayout.addWidget(self.styleMapStyleDrop, 0, 5)

        unitsPerEmLabel = QLabel("Units per em:", self)
        unitsPerEm = str(font.info.unitsPerEm) if font.info.unitsPerEm is not None else ''
        self.unitsPerEmEdit = QLineEdit(unitsPerEm, self)
        validator = QIntValidator(self)
        validator.setBottom(0)
        self.unitsPerEmEdit.setValidator(validator)

        ascenderLabel = QLabel("Ascender:", self)
        ascender = str(font.info.ascender) if font.info.ascender is not None else ''
        self.ascenderEdit = QLineEdit(ascender, self)
        self.ascenderEdit.setValidator(QIntValidator(self))

        capHeightLabel = QLabel("Cap height:", self)
        capHeight = str(font.info.capHeight) if font.info.capHeight is not None else ''
        self.capHeightEdit = QLineEdit(capHeight, self)
        self.capHeightEdit.setValidator(QIntValidator(self))

        mainLayout.addWidget(unitsPerEmLabel, 1, 0)
        mainLayout.addWidget(self.unitsPerEmEdit, 1, 1)
        mainLayout.addWidget(ascenderLabel, 1, 2)
        mainLayout.addWidget(self.ascenderEdit, 1, 3)
        mainLayout.addWidget(capHeightLabel, 1, 4)
        mainLayout.addWidget(self.capHeightEdit, 1, 5)

        italicAngleLabel = QLabel("Italic angle:", self)
        italicAngle = str(font.info.italicAngle) if font.info.italicAngle is not None else ''
        self.italicAngleEdit = QLineEdit(italicAngle, self)
        self.italicAngleEdit.setValidator(QDoubleValidator(self))

        descenderLabel = QLabel("Descender:", self)
        descender = str(font.info.descender) if font.info.descender is not None else ''
        self.descenderEdit = QLineEdit(descender, self)
        self.descenderEdit.setValidator(QIntValidator(self))

        xHeightLabel = QLabel("x-height:", self)
        xHeight = str(font.info.xHeight) if font.info.xHeight is not None else ''
        self.xHeightEdit = QLineEdit(xHeight, self)
        self.xHeightEdit.setValidator(QIntValidator(self))

        mainLayout.addWidget(italicAngleLabel, 2, 0)
        mainLayout.addWidget(self.italicAngleEdit, 2, 1)
        mainLayout.addWidget(descenderLabel, 2, 2)
        mainLayout.addWidget(self.descenderEdit, 2, 3)
        mainLayout.addWidget(xHeightLabel, 2, 4)
        mainLayout.addWidget(self.xHeightEdit, 2, 5)

        noteLabel = QLabel("Note:", self)
        self.noteEdit = QPlainTextEdit(font.info.note, self)

        mainLayout.addWidget(noteLabel, 3, 0)
        mainLayout.addWidget(self.noteEdit, 3, 1, 1, 5)

        self.setLayout(mainLayout)

    def writeValues(self, font):
        styleMapFamilyName = self.styleMapFamilyEdit.text()
        font.info.styleMapFamilyName = styleMapFamilyName if styleMapFamilyName != '' else None
        sn = self.styleMapStyleDrop.currentIndex()
        if sn == 1: font.info.styleMapStyleName = "regular"
        elif sn == 2: font.info.styleMapStyleName = "italic"
        elif sn == 3: font.info.styleMapStyleName = "bold"
        elif sn == 4: font.info.styleMapStyleName = "bold italic"
        else: font.info.styleMapStyleName = None
        unitsPerEm = self.unitsPerEmEdit.text()
        font.info.unitsPerEm = float(unitsPerEm) if "." in unitsPerEm else int(unitsPerEm) if unitsPerEm else None
        italicAngle = self.italicAngleEdit.text()
        font.info.italicAngle = float(italicAngle) if "." in italicAngle else int(italicAngle) if italicAngle else None
        ascender = self.ascenderEdit.text()
        font.info.ascender = float(ascender) if "." in ascender else int(ascender) if ascender else None
        descender = self.descenderEdit.text()
        font.info.descender = float(descender) if "." in descender else int(descender) if descender else None
        capHeight = self.capHeightEdit.text()
        font.info.capHeight = float(capHeight) if "." in capHeight else int(capHeight) if capHeight else None
        xHeight = self.xHeightEdit.text()
        font.info.xHeight = float(xHeight) if "." in xHeight else int(xHeight) if xHeight else None
        note = self.noteEdit.toPlainText()
        font.info.note = note if note != '' else None

class OpenTypeTab(QWidget):
    name = "OpenType"

    def __init__(self, font, parent=None):
        super(OpenTypeTab, self).__init__(parent)

        nameGroup = QGroupBox("name table", self)
        #nameGroup.setFlat(True)
        nameLayout = QGridLayout(self)

        preferredFamilyNameLabel = QLabel("Pref. Family Name:", self)
        self.preferredFamilyNameEdit = QLineEdit(font.info.openTypeNamePreferredFamilyName, self)

        preferredSubfamilyNameLabel = QLabel("Pref. Subfamily Name:", self)
        self.preferredSubfamilyNameEdit = QLineEdit(font.info.openTypeNamePreferredSubfamilyName, self)

        compatibleFullNameLabel = QLabel("Compatible Full Name:", self)
        self.compatibleFullNameEdit = QLineEdit(font.info.openTypeNameCompatibleFullName, self)

        WWSFamilyNameLabel = QLabel("WWS Family Name:", self)
        self.WWSFamilyNameEdit = QLineEdit(font.info.openTypeNameWWSFamilyName, self)

        WWSSubfamilyNameLabel = QLabel("WWS Subfamily Name:", self)
        self.WWSSubfamilyNameEdit = QLineEdit(font.info.openTypeNameWWSSubfamilyName, self)

        versionLabel = QLabel("Version:", self)
        self.versionEdit = QLineEdit(font.info.openTypeNameVersion, self)

        uniqueIDLabel = QLabel("Unique ID:", self)
        self.uniqueIDEdit = QLineEdit(font.info.openTypeNameUniqueID, self)

        descriptionLabel = QLabel("Description:", self)
        self.descriptionEdit = QLineEdit(font.info.openTypeNameDescription, self)

        sampleTextLabel = QLabel("Sample text:", self)
        self.sampleTextEdit = QLineEdit(font.info.openTypeNameSampleText, self)

        l = 0
        nameLayout.addWidget(preferredFamilyNameLabel, l, 0)
        nameLayout.addWidget(self.preferredFamilyNameEdit, l, 1, 1, 2)
        nameLayout.addWidget(WWSFamilyNameLabel, l, 3)
        nameLayout.addWidget(self.WWSFamilyNameEdit, l, 4, 1, 2)
        l += 1
        nameLayout.addWidget(preferredSubfamilyNameLabel, l, 0)
        nameLayout.addWidget(self.preferredSubfamilyNameEdit, l, 1, 1, 2)
        nameLayout.addWidget(WWSSubfamilyNameLabel, l, 3)
        nameLayout.addWidget(self.WWSSubfamilyNameEdit, l, 4, 1, 2)
        l += 1
        nameLayout.addWidget(compatibleFullNameLabel, l, 0)
        nameLayout.addWidget(self.compatibleFullNameEdit, l, 1, 1, 2)
        l += 1
        nameLayout.addWidget(versionLabel, l, 0)
        nameLayout.addWidget(self.versionEdit, l, 1, 1, 2)
        nameLayout.addWidget(uniqueIDLabel, l, 3)
        nameLayout.addWidget(self.uniqueIDEdit, l, 4, 1, 2)
        l += 1
        nameLayout.addWidget(descriptionLabel, l, 0)
        nameLayout.addWidget(self.descriptionEdit, l, 1, 1, 2)
        nameLayout.addWidget(sampleTextLabel, l, 3)
        nameLayout.addWidget(self.sampleTextEdit, l, 4, 1, 2)
        nameGroup.setLayout(nameLayout)

        hheaGroup = QGroupBox("hhea table", self)
        #hheaGroup.setFlat(True)
        hheaLayout = QGridLayout(self)

        ascenderLabel = QLabel("Ascender:", self)
        ascender = str(font.info.openTypeHheaAscender) if font.info.openTypeHheaAscender is not None else ''
        self.ascenderEdit = QLineEdit(ascender, self)
        self.ascenderEdit.setValidator(QIntValidator(self))

        descenderLabel = QLabel("Descender:", self)
        descender = str(font.info.openTypeHheaDescender) if font.info.openTypeHheaDescender is not None else ''
        self.descenderEdit = QLineEdit(descender, self)
        self.descenderEdit.setValidator(QIntValidator(self))

        lineGapLabel = QLabel("LineGap:", self)
        lineGap = str(font.info.openTypeHheaLineGap) if font.info.openTypeHheaLineGap is not None else ''
        self.lineGapEdit = QLineEdit(lineGap, self)
        self.lineGapEdit.setValidator(QIntValidator(self))

        caretSlopeRiseLabel = QLabel("caretSlopeRise:", self)
        caretSlopeRise = str(font.info.openTypeHheaCaretSlopeRise) if font.info.openTypeHheaCaretSlopeRise is not None else ''
        self.caretSlopeRiseEdit = QLineEdit(caretSlopeRise, self)
        self.caretSlopeRiseEdit.setValidator(QIntValidator(self))

        caretSlopeRunLabel = QLabel("caretSlopeRun:", self)
        caretSlopeRun = str(font.info.openTypeHheaCaretSlopeRun) if font.info.openTypeHheaCaretSlopeRun is not None else ''
        self.caretSlopeRunEdit = QLineEdit(caretSlopeRun, self)
        self.caretSlopeRunEdit.setValidator(QIntValidator(self))

        caretOffsetLabel = QLabel("caretOffset:", self)
        caretOffset = str(font.info.openTypeHheaCaretOffset) if font.info.openTypeHheaCaretOffset is not None else ''
        self.caretOffsetEdit = QLineEdit(caretOffset, self)
        self.caretOffsetEdit.setValidator(QIntValidator(self))

        l = 0
        hheaLayout.addWidget(ascenderLabel, l, 0)
        hheaLayout.addWidget(self.ascenderEdit, l, 1, 1, 2)
        hheaLayout.addWidget(caretSlopeRiseLabel, l, 3)
        hheaLayout.addWidget(self.caretSlopeRiseEdit, l, 4, 1, 2)
        l += 1
        hheaLayout.addWidget(descenderLabel, l, 0)
        hheaLayout.addWidget(self.descenderEdit, l, 1, 1, 2)
        hheaLayout.addWidget(caretSlopeRunLabel, l, 3)
        hheaLayout.addWidget(self.caretSlopeRunEdit, l, 4, 1, 2)
        l += 1
        hheaLayout.addWidget(lineGapLabel, l, 0)
        hheaLayout.addWidget(self.lineGapEdit, l, 1, 1, 2)
        hheaLayout.addWidget(caretOffsetLabel, l, 3)
        hheaLayout.addWidget(self.caretOffsetEdit, l, 4, 1, 2)
        hheaGroup.setLayout(hheaLayout)

        vheaGroup = QGroupBox("vhea table", self)
        #vheaGroup.setFlat(True)
        vheaLayout = QGridLayout(self)

        vertTypoAscenderLabel = QLabel("vertTypoAscender:", self)
        vertTypoAscender = str(font.info.openTypeVheaVertTypoAscender) if font.info.openTypeVheaVertTypoAscender is not None else ''
        self.vertTypoAscenderEdit = QLineEdit(vertTypoAscender, self)
        self.vertTypoAscenderEdit.setValidator(QIntValidator(self))

        vertTypoDescenderLabel = QLabel("vertTypoDescender:", self)
        vertTypoDescender = str(font.info.openTypeVheaVertTypoDescender) if font.info.openTypeVheaVertTypoDescender is not None else ''
        self.vertTypoDescenderEdit = QLineEdit(vertTypoDescender, self)
        self.vertTypoDescenderEdit.setValidator(QIntValidator(self))

        vertTypoLineGapLabel = QLabel("vertTypoLineGap:", self)
        vertTypoLineGap = str(font.info.openTypeVheaVertTypoLineGap) if font.info.openTypeVheaVertTypoLineGap is not None else ''
        self.vertTypoLineGapEdit = QLineEdit(vertTypoLineGap, self)
        self.vertTypoLineGapEdit.setValidator(QIntValidator(self))

        vheaCaretSlopeRiseLabel = QLabel("caretSlopeRise:", self)
        vheaCaretSlopeRise = str(font.info.openTypeVheaCaretSlopeRise) if font.info.openTypeVheaCaretSlopeRise is not None else ''
        self.vheaCaretSlopeRiseEdit = QLineEdit(vheaCaretSlopeRise, self)
        self.vheaCaretSlopeRiseEdit.setValidator(QIntValidator(self))

        vheaCaretSlopeRunLabel = QLabel("caretSlopeRun:", self)
        vheaCaretSlopeRun = str(font.info.openTypeVheaCaretSlopeRun) if font.info.openTypeVheaCaretSlopeRun is not None else ''
        self.vheaCaretSlopeRunEdit = QLineEdit(vheaCaretSlopeRun, self)
        self.vheaCaretSlopeRunEdit.setValidator(QIntValidator(self))

        vheaCaretOffsetLabel = QLabel("caretOffset:", self)
        vheaCaretOffset = str(font.info.openTypeVheaCaretOffset) if font.info.openTypeVheaCaretOffset is not None else ''
        self.vheaCaretOffsetEdit = QLineEdit(vheaCaretOffset, self)
        self.vheaCaretOffsetEdit.setValidator(QIntValidator(self))

        l = 0
        vheaLayout.addWidget(vertTypoAscenderLabel, l, 0)
        vheaLayout.addWidget(self.vertTypoAscenderEdit, l, 1, 1, 2)
        vheaLayout.addWidget(vheaCaretSlopeRiseLabel, l, 3)
        vheaLayout.addWidget(self.vheaCaretSlopeRiseEdit, l, 4, 1, 2)
        l += 1
        vheaLayout.addWidget(vertTypoDescenderLabel, l, 0)
        vheaLayout.addWidget(self.vertTypoDescenderEdit, l, 1, 1, 2)
        vheaLayout.addWidget(vheaCaretSlopeRunLabel, l, 3)
        vheaLayout.addWidget(self.vheaCaretSlopeRunEdit, l, 4, 1, 2)
        l += 1
        vheaLayout.addWidget(vertTypoLineGapLabel, l, 0)
        vheaLayout.addWidget(self.vertTypoLineGapEdit, l, 1, 1, 2)
        vheaLayout.addWidget(vheaCaretOffsetLabel, l, 3)
        vheaLayout.addWidget(self.vheaCaretOffsetEdit, l, 4, 1, 2)
        vheaGroup.setLayout(vheaLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(nameGroup)
        mainLayout.addWidget(hheaGroup)
        mainLayout.addWidget(vheaGroup)
        self.setLayout(mainLayout)

    def writeValues(self, font):
        preferredFamilyName = self.preferredFamilyNameEdit.text()
        font.info.openTypeNamePreferredFamilyName = preferredFamilyName if preferredFamilyName != '' else None
        preferredSubfamilyName = self.preferredSubfamilyNameEdit.text()
        font.info.openTypeNamePreferredSubfamilyName = preferredSubfamilyName if preferredSubfamilyName != '' else None
        WWSFamilyName = self.WWSFamilyNameEdit.text()
        font.info.openTypeNameWWSFamilyName = WWSFamilyName if WWSFamilyName != '' else None
        WWSSubfamilyName = self.WWSSubfamilyNameEdit.text()
        font.info.openTypeNameWWSSubfamilyName = WWSSubfamilyName if WWSSubfamilyName != '' else None
        compatibleFullName = self.compatibleFullNameEdit.text()
        font.info.openTypeNameCompatibleFullName = compatibleFullName if compatibleFullName != '' else None
        version = self.versionEdit.text()
        font.info.openTypeNameVersion = version if version != '' else None
        uniqueID = self.uniqueIDEdit.text()
        font.info.openTypeNameUniqueID = uniqueID if uniqueID != '' else None
        description = self.descriptionEdit.text()
        font.info.openTypeNameDescription = description if description != '' else None
        sampleText = self.sampleTextEdit.text()
        font.info.openTypeNameSampleText = sampleText if sampleText != '' else None
        ascender = self.ascenderEdit.text()
        font.info.openTypeHheaAscender = int(ascender) if ascender != '' else None
        descender = self.descenderEdit.text()
        font.info.openTypeHheaDescender = int(descender) if descender != '' else None
        lineGap = self.lineGapEdit.text()
        font.info.openTypeHheaLineGap = int(lineGap) if lineGap != '' else None
        caretSlopeRise = self.caretSlopeRiseEdit.text()
        font.info.openTypeHheaCaretSlopeRise = int(caretSlopeRise) if caretSlopeRise != '' else None
        caretSlopeRun = self.caretSlopeRunEdit.text()
        font.info.openTypeHheaCaretSlopeRun = int(caretSlopeRun) if caretSlopeRun != '' else None
        caretOffset = self.caretOffsetEdit.text()
        font.info.openTypeHheaCaretOffset = int(caretOffset) if caretOffset != '' else None
        vertTypoAscender = self.vertTypoAscenderEdit.text()
        font.info.openTypeVheaAscender = int(vertTypoAscender) if vertTypoAscender != '' else None
        vertTypoDescender = self.vertTypoDescenderEdit.text()
        font.info.openTypeVheaDescender = int(vertTypoDescender) if vertTypoDescender != '' else None
        vertTypoLineGap = self.vertTypoLineGapEdit.text()
        font.info.openTypeVheaLineGap = int(vertTypoLineGap) if vertTypoLineGap != '' else None
        vheaCaretSlopeRise = self.vheaCaretSlopeRiseEdit.text()
        font.info.openTypeVheaCaretSlopeRise = int(vheaCaretSlopeRise) if vheaCaretSlopeRise != '' else None
        vheaCaretSlopeRun = self.vheaCaretSlopeRunEdit.text()
        font.info.openTypeVheaCaretSlopeRun = int(vheaCaretSlopeRun) if vheaCaretSlopeRun != '' else None
        vheaCaretOffset = self.vheaCaretOffsetEdit.text()
        font.info.openTypeVheaCaretOffset = int(vheaCaretOffset) if vheaCaretOffset != '' else None

class PostScriptTab(QWidget):
    name = "Postscript"

    def __init__(self, font, parent=None):
        super(PostScriptTab, self).__init__(parent)

        namingGroup = QGroupBox("Naming", self)
        #namingGroup.setFlat(True)
        namingLayout = QGridLayout(self)

        fontNameLabel = QLabel("FontName:", self)
        self.fontNameEdit = QLineEdit(font.info.postscriptFontName, self)

        fullNameLabel = QLabel("FullName:", self)
        self.fullNameEdit = QLineEdit(font.info.postscriptFullName, self)

        weightNameLabel = QLabel("WeightName:", self)
        self.weightNameEdit = QLineEdit(font.info.postscriptWeightName, self)

        uniqueIDLabel = QLabel("Unique ID:", self)
        uniqueID = str(font.info.postscriptUniqueID) if font.info.postscriptUniqueID is not None else ''
        self.uniqueIDEdit = QLineEdit(uniqueID, self)
        self.uniqueIDEdit.setValidator(QIntValidator(self))

        l = 0
        namingLayout.addWidget(fontNameLabel, l, 0)
        namingLayout.addWidget(self.fontNameEdit, l, 1, 1, 2)
        namingLayout.addWidget(weightNameLabel, l, 3)
        namingLayout.addWidget(self.weightNameEdit, l, 4, 1, 2)
        l += 1
        namingLayout.addWidget(fullNameLabel, l, 0)
        namingLayout.addWidget(self.fullNameEdit, l, 1, 1, 2)
        namingLayout.addWidget(uniqueIDLabel, l, 3)
        namingLayout.addWidget(self.uniqueIDEdit, l, 4, 1, 2)
        namingGroup.setLayout(namingLayout)

        hintingGroup = QGroupBox("Hinting", self)
        #hintingGroup.setFlat(True)
        hintingLayout = QGridLayout(self)

        blueValuesLabel = QLabel("Blue values:", self)
        blueValues = " ".join(str(val) for val in font.info.postscriptBlueValues)
        self.blueValuesEdit = QLineEdit(blueValues, self)

        otherBluesLabel = QLabel("Other blues:", self)
        otherBlues = " ".join(str(val) for val in font.info.postscriptOtherBlues)
        self.otherBluesEdit = QLineEdit(otherBlues, self)

        familyBluesLabel = QLabel("Family blues:", self)
        familyBlues = " ".join(str(val) for val in font.info.postscriptFamilyBlues)
        self.familyBluesEdit = QLineEdit(familyBlues, self)

        familyOtherBluesLabel = QLabel("Family other blues:", self)
        familyOtherBlues = " ".join(str(val) for val in font.info.postscriptFamilyOtherBlues)
        self.familyOtherBluesEdit = QLineEdit(familyOtherBlues, self)

        l = 0
        hintingLayout.addWidget(blueValuesLabel, l, 0)
        hintingLayout.addWidget(self.blueValuesEdit, l, 1, 1, 2)
        hintingLayout.addWidget(familyBluesLabel, l, 3)
        hintingLayout.addWidget(self.familyBluesEdit, l, 4, 1, 2)
        l += 1
        hintingLayout.addWidget(otherBluesLabel, l, 0)
        hintingLayout.addWidget(self.otherBluesEdit, l, 1, 1, 2)
        hintingLayout.addWidget(familyOtherBluesLabel, l, 3)
        hintingLayout.addWidget(self.familyOtherBluesEdit, l, 4, 1, 2)
        l += 1

        blueFuzzLabel = QLabel("Blue fuzz:", self)
        blueFuzz = str(font.info.postscriptBlueFuzz) if font.info.postscriptBlueFuzz is not None else ''
        self.blueFuzzEdit = QLineEdit(blueFuzz, self)
        self.blueFuzzEdit.setValidator(QDoubleValidator(self))

        stemSnapHLabel = QLabel("StemSnapH:", self)
        stemSnapH = " ".join(str(val) for val in font.info.postscriptStemSnapH)
        self.stemSnapHEdit = QLineEdit(stemSnapH, self)

        blueScaleLabel = QLabel("Blue scale:", self)
        blueScale = str(font.info.postscriptBlueScale) if font.info.postscriptBlueScale is not None else ''
        self.blueScaleEdit = QLineEdit(blueScale, self)
        self.blueScaleEdit.setValidator(QDoubleValidator(self))

        stemSnapVLabel = QLabel("StemSnapV:", self)
        stemSnapV = " ".join(str(val) for val in font.info.postscriptStemSnapV)
        self.stemSnapVEdit = QLineEdit(stemSnapV, self)

        blueShiftLabel = QLabel("Blue shift:", self)
        blueShift = str(font.info.postscriptBlueShift) if font.info.postscriptBlueShift is not None else ''
        self.blueShiftEdit = QLineEdit(blueShift, self)
        self.blueShiftEdit.setValidator(QDoubleValidator(self))

        forceBoldLabel = QLabel("Force bold:", self)
        forceBold = font.info.postscriptForceBold
        self.forceBoldBox = QCheckBox(self)
        self.forceBoldBox.setTristate()
        if forceBold is None: self.forceBoldBox.setCheckState(Qt.PartiallyChecked)
        else: self.forceBoldBox.setChecked(forceBold)

        hintingLayout.addWidget(blueFuzzLabel, l, 0)
        hintingLayout.addWidget(self.blueFuzzEdit, l, 1, 1, 2)
        hintingLayout.addWidget(stemSnapHLabel, l, 3)
        hintingLayout.addWidget(self.stemSnapHEdit, l, 4, 1, 2)
        l += 1
        hintingLayout.addWidget(blueScaleLabel, l, 0)
        hintingLayout.addWidget(self.blueScaleEdit, l, 1, 1, 2)
        hintingLayout.addWidget(stemSnapVLabel, l, 3)
        hintingLayout.addWidget(self.stemSnapVEdit, l, 4, 1, 2)
        l += 1
        hintingLayout.addWidget(blueShiftLabel, l, 0)
        hintingLayout.addWidget(self.blueShiftEdit, l, 1, 1, 2)
        hintingLayout.addWidget(forceBoldLabel, l, 3)
        hintingLayout.addWidget(self.forceBoldBox, l, 4, 1, 2)
        hintingGroup.setLayout(hintingLayout)

        metricsGroup = QGroupBox("Metrics", self)
        #metricsGroup.setFlat(True)
        metricsLayout = QGridLayout(self)

        defaultWidthXLabel = QLabel("DefaultWidthX:", self)
        defaultWidthX = str(font.info.postscriptDefaultWidthX) if font.info.postscriptDefaultWidthX is not None else ''
        self.defaultWidthXEdit = QLineEdit(defaultWidthX, self)
        self.defaultWidthXEdit.setValidator(QDoubleValidator(self))

        underlineThicknessLabel = QLabel("UnderlineThickness:", self)
        underlineThickness = str(font.info.postscriptUnderlineThickness) if font.info.postscriptUnderlineThickness is not None else ''
        self.underlineThicknessEdit = QLineEdit(underlineThickness, self)
        self.underlineThicknessEdit.setValidator(QDoubleValidator(self))

        nominalWidthXLabel = QLabel("NominalWidthX:", self)
        nominalWidthX = str(font.info.postscriptNominalWidthX) if font.info.postscriptNominalWidthX is not None else ''
        self.nominalWidthXEdit = QLineEdit(nominalWidthX, self)
        self.nominalWidthXEdit.setValidator(QDoubleValidator(self))

        underlinePositionLabel = QLabel("UnderlinePosition:", self)
        underlinePosition = str(font.info.postscriptUnderlinePosition) if font.info.postscriptUnderlinePosition is not None else ''
        self.underlinePositionEdit = QLineEdit(underlinePosition, self)
        self.underlinePositionEdit.setValidator(QDoubleValidator(self))

        slantAngleLabel = QLabel("SlantAngle:", self)
        slantAngle = str(font.info.postscriptSlantAngle) if font.info.postscriptSlantAngle is not None else ''
        self.slantAngleEdit = QLineEdit(slantAngle, self)
        self.slantAngleEdit.setValidator(QDoubleValidator(self))

        isFixedPitchLabel = QLabel("isFixedPitched:", self)
        isFixedPitch = font.info.postscriptIsFixedPitch
        self.isFixedPitchBox = QCheckBox(self)
        self.isFixedPitchBox.setTristate()
        if isFixedPitch is None: self.isFixedPitchBox.setCheckState(Qt.PartiallyChecked)
        else: self.isFixedPitchBox.setChecked(isFixedPitch)

        l = 0
        metricsLayout.addWidget(defaultWidthXLabel, l, 0)
        metricsLayout.addWidget(self.defaultWidthXEdit, l, 1, 1, 2)
        metricsLayout.addWidget(underlineThicknessLabel, l, 3)
        metricsLayout.addWidget(self.underlineThicknessEdit, l, 4, 1, 2)
        l += 1
        metricsLayout.addWidget(nominalWidthXLabel, l, 0)
        metricsLayout.addWidget(self.nominalWidthXEdit, l, 1, 1, 2)
        metricsLayout.addWidget(underlinePositionLabel, l, 3)
        metricsLayout.addWidget(self.underlinePositionEdit, l, 4, 1, 2)
        l += 1
        metricsLayout.addWidget(slantAngleLabel, l, 0)
        metricsLayout.addWidget(self.slantAngleEdit, l, 1, 1, 2)
        metricsLayout.addWidget(isFixedPitchLabel, l, 3)
        metricsLayout.addWidget(self.isFixedPitchBox, l, 4, 1, 2)
        metricsGroup.setLayout(metricsLayout)

        charactersGroup = QGroupBox("Characters", self)
        #charactersGroup.setFlat(True)
        charactersLayout = QGridLayout(self)

        defaultCharacterLabel = QLabel("Default character:", self)
        self.defaultCharacterEdit = QLineEdit(font.info.postscriptDefaultCharacter, self)

        windowsCharacterSetLabel = QLabel("Windows character set:", self)
        self.windowsCharacterSetDrop = QComboBox(self)
        items = ["None", "ANSI", "Default", "Symbol", "Macintosh", "Shift JIS", "Hangul", "Hangul (Johab)", "GB2312",
            "Chinese BIG5", "Greek", "Turkish", "Vietnamese", "Hebrew", "Arabic", "Baltic", "Bitstream",
            "Cyrillic", "Thai", "Eastern European", "OEM"]
        self.windowsCharacterSetDrop.insertItems(0, items)
        if font.info.postscriptWindowsCharacterSet is not None:
            self.windowsCharacterSetDrop.setCurrentIndex(font.info.postscriptWindowsCharacterSet)

        l = 0
        charactersLayout.addWidget(defaultCharacterLabel, l, 0)
        charactersLayout.addWidget(self.defaultCharacterEdit, l, 1, 1, 2)
        charactersLayout.addWidget(windowsCharacterSetLabel, l, 3)
        charactersLayout.addWidget(self.windowsCharacterSetDrop, l, 4, 1, 2)
        charactersGroup.setLayout(charactersLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(namingGroup)
        mainLayout.addWidget(hintingGroup)
        mainLayout.addWidget(metricsGroup)
        mainLayout.addWidget(charactersGroup)
        self.setLayout(mainLayout)

    def writeValues(self, font):
        fontName = self.fontNameEdit.text()
        font.info.postscriptFontName = fontName if fontName != '' else None
        fullName = self.fullNameEdit.text()
        font.info.postscriptFullName = fullName if fullName != '' else None
        weightName = self.weightNameEdit.text()
        font.info.postscriptWeightName = weightName if weightName != '' else None
        uniqueID = self.uniqueIDEdit.text()
        font.info.postscriptUniqueID = int(uniqueID) if uniqueID != '' else None
        blueValues = self.blueValuesEdit.text().split(" ")
        if blueValues is None:
            font.info.postscriptBlueValues = None
        else:
            blues = []
            for blue in blueValues:
                if blue != '':
                    blues.append(int(blue))
            font.info.postscriptBlueValues = blues
        otherBlues = self.otherBluesEdit.text().split(" ")
        if otherBlues is None:
            font.info.postscriptOtherBlues = None
        else:
            blues = []
            for blue in otherBlues:
                if blue != '':
                    blues.append(int(blue))
            font.info.postscriptOtherBlues = blues
        familyBlues = self.familyBluesEdit.text().split(" ")
        if familyBlues is None:
            font.info.postscriptFamilyBlues = None
        else:
            blues = []
            for blue in familyBlues:
                if blue != '':
                    blues.append(int(blue))
            font.info.postscriptFamilyBlues = blues
        familyOtherBlues = self.familyOtherBluesEdit.text().split(" ")
        if familyOtherBlues is None:
            font.info.postscriptFamilyOtherBlues = None
        else:
            blues = []
            for blue in familyOtherBlues:
                if blue != '':
                    blues.append(int(blue))
            font.info.postscriptFamilyOtherBlues = blues
        blueFuzz = self.blueFuzzEdit.text()
        font.info.postscriptBlueFuzz = float(blueFuzz) if "." in blueFuzz else int(blueFuzz) if blueFuzz != '' else None
        blueScale = self.blueScaleEdit.text()
        font.info.postscriptBlueScale = float(blueScale) if blueScale != '' else None
        blueShift = self.blueShiftEdit.text()
        font.info.postscriptBlueShift = float(blueShift) if "." in blueShift else int(blueShift) if blueShift != '' else None
        stemSnapH = self.stemSnapHEdit.text().split(" ")
        if stemSnapH is None:
            font.info.postscriptStemSnapH = None
        else:
            stems = []
            for stem in stemSnapH:
                if stem != '':
                    stems.append(int(stem))
            font.info.postscriptStemSnapH = stems
        stemSnapV = self.stemSnapVEdit.text().split(" ")
        if stemSnapV is None:
            font.info.postscriptStemSnapV = None
        else:
            stems = []
            for stem in stemSnapV:
                if stem != '':
                    stems.append(int(stem))
            font.info.postscriptStemSnapV = stems
        forceBold = self.forceBoldBox.checkState()
        if forceBold == Qt.PartiallyChecked:
            font.info.postscriptForceBold = None
        else:
            font.info.postscriptForceBold = bool(forceBold)
        defaultWidthX = self.defaultWidthXEdit.text()
        font.info.postscriptDefaultWidthX = float(defaultWidthX) if "." in defaultWidthX else int(defaultWidthX) if defaultWidthX != '' else None
        nominalWidthX = self.nominalWidthXEdit.text()
        font.info.postscriptNominalWidthX = float(nominalWidthX) if "." in nominalWidthX else int(nominalWidthX) if nominalWidthX != '' else None
        underlineThickness = self.underlineThicknessEdit.text()
        font.info.postscriptUnderlineThickness = float(underlineThickness) if "." in underlineThickness else int(underlineThickness) if underlineThickness != '' else None
        underlinePosition = self.underlinePositionEdit.text()
        font.info.postscriptUnderlinePosition = float(underlinePosition) if "." in underlinePosition else int(underlinePosition) if underlinePosition != '' else None
        slantAngle = self.slantAngleEdit.text()
        font.info.postscriptSlantAngle = float(slantAngle) if "." in slantAngle else int(slantAngle) if slantAngle != '' else None
        isFixedPitch = self.isFixedPitchBox.checkState()
        if isFixedPitch == Qt.PartiallyChecked:
            font.info.postscriptIsFixedPitch = None
        else:
            font.info.postscriptIsFixedPitch = bool(isFixedPitch)
        defaultCharacter = self.defaultCharacterEdit.text()
        font.info.postscriptDefaultCharacter = defaultCharacter if defaultCharacter != '' else None
        windowsCharacterSet = self.windowsCharacterSetDrop.currentIndex()
        if windowsCharacterSet == 0:
            font.info.postscriptWindowsCharacterSet = None
        else:
            font.info.postscriptWindowsCharacterSet = windowsCharacterSet
