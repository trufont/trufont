from PyQt5.QtCore import QDate, QDateTime, QTime, Qt
from PyQt5.QtGui import (
    QDoubleValidator, QIntValidator, QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox,
    QGridLayout, QGroupBox, QLabel, QLineEdit, QListView, QPlainTextEdit,
    QTabWidget, QVBoxLayout, QWidget)


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
        self.tabWidget.addNamedTab(OS2Tab(self.font))
        self.tabWidget.addNamedTab(PostScriptTab(self.font))

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Font Info – %s %s" % (
            self.font.info.familyName, self.font.info.styleName))

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
        self.designerURLEdit = QLineEdit(
            font.info.openTypeNameDesignerURL, self)

        mainLayout.addWidget(designerURLLabel, 2, 0)
        mainLayout.addWidget(self.designerURLEdit, 2, 1, 1, 5)

        manufacturerLabel = QLabel("Manufacturer:", self)
        self.manufacturerEdit = QLineEdit(
            font.info.openTypeNameManufacturer, self)

        mainLayout.addWidget(manufacturerLabel, 3, 0)
        mainLayout.addWidget(self.manufacturerEdit, 3, 1, 1, 5)

        manufacturerURLLabel = QLabel("Manufacturer URL:", self)
        self.manufacturerURLEdit = QLineEdit(
            font.info.openTypeNameManufacturerURL, self)

        mainLayout.addWidget(manufacturerURLLabel, 4, 0)
        mainLayout.addWidget(self.manufacturerURLEdit, 4, 1, 1, 5)

        copyrightLabel = QLabel("Copyright:", self)
        self.copyrightEdit = QLineEdit(font.info.copyright, self)

        mainLayout.addWidget(copyrightLabel, 5, 0)
        mainLayout.addWidget(self.copyrightEdit, 5, 1, 1, 5)

        # TODO: give visual feedback of input data validity using QLineEdit
        # lose focus event
        # http://snorf.net/blog/2014/08/09/using-qvalidator-in-pyqt4-to-validate-user-input/ # noqa
        versionLabel = QLabel("Version:", self)
        if font.info.versionMajor is not None:
            versionMajor = str(font.info.versionMajor)
        else:
            versionMajor = ''
        self.versionMajorEdit = QLineEdit(versionMajor, self)
        self.versionMajorEdit.setAlignment(Qt.AlignRight)
        self.versionMajorEdit.setValidator(QIntValidator(self))
        versionDotLabel = QLabel(".", self)
        if font.info.versionMinor is not None:
            versionMinor = str(font.info.versionMinor)
        else:
            versionMinor = ''
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
        # dateTime.fromString(font.info.openTypeHeadCreated, "yyyy/MM/dd
        # hh:mm:ss") # XXX: why does this not work?
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
        if familyName != '':
            font.info.familyName = familyName
        else:
            font.info.trademark = None
        styleName = self.styleNameEdit.text()
        if styleName != '':
            font.info.styleName = styleName
        else:
            font.info.trademark = None
        designer = self.designerEdit.text()
        if designer != '':
            font.info.openTypeNameDesigner = designer
        else:
            font.info.trademark = None
        designerURL = self.designerURLEdit.text()
        if designerURL != '':
            font.info.openTypeNameDesignerURL = designerURL
        else:
            font.info.trademark = None
        manufacturer = self.manufacturerEdit.text()
        if manufacturer != '':
            font.info.openTypeNameManufacturer = manufacturer
        else:
            font.info.trademark = None
        manufacturerURL = self.manufacturerURLEdit.text()
        if manufacturerURL != '':
            font.info.openTypeNameManufacturerURL = manufacturerURL
        else:
            font.info.trademark = None
        copyright = self.copyrightEdit.text()
        if copyright != '':
            font.info.copyright = copyright
        else:
            font.info.trademark = None
        versionMajor = self.versionMajorEdit.text()
        if versionMajor:
            font.info.versionMajor = int(versionMajor)
        else:
            font.info.versionMajor = None
        versionMinor = self.versionMinorEdit.text()
        if versionMinor:
            font.info.versionMinor = int(versionMinor)
        else:
            font.info.versionMinor = None
        font.info.openTypeHeadCreated = self.dateCreatedEdit.dateTime(
        ).toString("yyyy/MM/dd hh:mm:ss")
        license = self.licenseEdit.text()
        if license != '':
            font.info.openTypeNameLicense = license
        else:
            font.info.trademark = None
        licenseURL = self.licenseURLEdit.text()
        if licenseURL != '':
            font.info.openTypeNameLicenseURL = licenseURL
        else:
            font.info.trademark = None
        trademark = self.trademarkEdit.text()
        if trademark != '':
            font.info.trademark = trademark
        else:
            font.info.trademark = None


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
        if sn == "regular":
            self.styleMapStyleDrop.setCurrentIndex(1)
        elif sn == "regular italic":
            self.styleMapStyleDrop.setCurrentIndex(2)
        elif sn == "bold":
            self.styleMapStyleDrop.setCurrentIndex(3)
        elif sn == "bold italic":
            self.styleMapStyleDrop.setCurrentIndex(4)
        else:
            self.styleMapStyleDrop.setCurrentIndex(0)

        mainLayout.addWidget(styleMapFamilyLabel, 0, 0)
        mainLayout.addWidget(self.styleMapFamilyEdit, 0, 1, 1, 3)
        mainLayout.addWidget(styleMapStyleLabel, 0, 4)
        mainLayout.addWidget(self.styleMapStyleDrop, 0, 5)

        unitsPerEmLabel = QLabel("Units per em:", self)
        unitsPerEm = str(
            font.info.unitsPerEm) if font.info.unitsPerEm is not None else ''
        self.unitsPerEmEdit = QLineEdit(unitsPerEm, self)
        validator = QIntValidator(self)
        validator.setBottom(0)
        self.unitsPerEmEdit.setValidator(validator)

        ascenderLabel = QLabel("Ascender:", self)
        ascender = str(
            font.info.ascender) if font.info.ascender is not None else ''
        self.ascenderEdit = QLineEdit(ascender, self)
        self.ascenderEdit.setValidator(QIntValidator(self))

        capHeightLabel = QLabel("Cap height:", self)
        capHeight = str(
            font.info.capHeight) if font.info.capHeight is not None else ''
        self.capHeightEdit = QLineEdit(capHeight, self)
        self.capHeightEdit.setValidator(QIntValidator(self))

        mainLayout.addWidget(unitsPerEmLabel, 1, 0)
        mainLayout.addWidget(self.unitsPerEmEdit, 1, 1)
        mainLayout.addWidget(ascenderLabel, 1, 2)
        mainLayout.addWidget(self.ascenderEdit, 1, 3)
        mainLayout.addWidget(capHeightLabel, 1, 4)
        mainLayout.addWidget(self.capHeightEdit, 1, 5)

        italicAngleLabel = QLabel("Italic angle:", self)
        italicAngle = str(
            font.info.italicAngle) if font.info.italicAngle is not None else ''
        self.italicAngleEdit = QLineEdit(italicAngle, self)
        self.italicAngleEdit.setValidator(QDoubleValidator(self))

        descenderLabel = QLabel("Descender:", self)
        descender = str(
            font.info.descender) if font.info.descender is not None else ''
        self.descenderEdit = QLineEdit(descender, self)
        self.descenderEdit.setValidator(QIntValidator(self))

        xHeightLabel = QLabel("x-height:", self)
        xHeight = str(
            font.info.xHeight) if font.info.xHeight is not None else ''
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
        if styleMapFamilyName != '':
            font.info.styleMapFamilyName = styleMapFamilyName
        else:
            font.info.styleMapFamilyName = None
        sn = self.styleMapStyleDrop.currentIndex()
        if sn == 1:
            font.info.styleMapStyleName = "regular"
        elif sn == 2:
            font.info.styleMapStyleName = "italic"
        elif sn == 3:
            font.info.styleMapStyleName = "bold"
        elif sn == 4:
            font.info.styleMapStyleName = "bold italic"
        else:
            font.info.styleMapStyleName = None
        unitsPerEm = self.unitsPerEmEdit.text()
        if "." in unitsPerEm:
            font.info.unitsPerEm = float(unitsPerEm)
        elif unitsPerEm:
            font.info.unitsPerEm = int(unitsPerEm)
        else:
            font.info.unitsPerEm = None
        italicAngle = self.italicAngleEdit.text()
        if "." in italicAngle:
            font.info.italicAngle = float(italicAngle)
        elif italicAngle:
            font.info.italicAngle = int(italicAngle)
        else:
            font.info.italicAngle = None
        ascender = self.ascenderEdit.text()
        if "." in ascender:
            font.info.ascender = float(ascender)
        elif ascender:
            font.info.ascender = int(ascender)
        else:
            font.info.ascender = None
        descender = self.descenderEdit.text()
        if "." in descender:
            font.info.descender = float(descender)
        elif descender:
            font.info.descender = int(descender)
        else:
            font.info.descender = None
        capHeight = self.capHeightEdit.text()
        if "." in capHeight:
            font.info.capHeight = float(capHeight)
        elif capHeight:
            font.info.capHeight = int(capHeight)
        else:
            font.info.capHeight = None
        xHeight = self.xHeightEdit.text()
        if "." in xHeight:
            font.info.xHeight = float(xHeight)
        elif xHeight:
            font.info.xHeight = int(xHeight)
        else:
            font.info.xHeight = None
        note = self.noteEdit.toPlainText()
        if note != '':
            font.info.note = note
        else:
            font.info.note = None


class OpenTypeTab(QWidget):
    name = "OpenType"

    def __init__(self, font, parent=None):
        super(OpenTypeTab, self).__init__(parent)

        nameGroup = QGroupBox("name table", self)
        # nameGroup.setFlat(True)
        nameLayout = QGridLayout(self)

        preferredFamilyNameLabel = QLabel("Pref. Family Name:", self)
        self.preferredFamilyNameEdit = QLineEdit(
            font.info.openTypeNamePreferredFamilyName, self)

        preferredSubfamilyNameLabel = QLabel("Pref. Subfamily Name:", self)
        self.preferredSubfamilyNameEdit = QLineEdit(
            font.info.openTypeNamePreferredSubfamilyName, self)

        compatibleFullNameLabel = QLabel("Compatible Full Name:", self)
        self.compatibleFullNameEdit = QLineEdit(
            font.info.openTypeNameCompatibleFullName, self)

        WWSFamilyNameLabel = QLabel("WWS Family Name:", self)
        self.WWSFamilyNameEdit = QLineEdit(
            font.info.openTypeNameWWSFamilyName, self)

        WWSSubfamilyNameLabel = QLabel("WWS Subfamily Name:", self)
        self.WWSSubfamilyNameEdit = QLineEdit(
            font.info.openTypeNameWWSSubfamilyName, self)

        versionLabel = QLabel("Version:", self)
        self.versionEdit = QLineEdit(font.info.openTypeNameVersion, self)

        uniqueIDLabel = QLabel("Unique ID:", self)
        self.uniqueIDEdit = QLineEdit(font.info.openTypeNameUniqueID, self)

        descriptionLabel = QLabel("Description:", self)
        self.descriptionEdit = QLineEdit(
            font.info.openTypeNameDescription, self)

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
        # hheaGroup.setFlat(True)
        hheaLayout = QGridLayout(self)

        ascenderLabel = QLabel("Ascender:", self)
        if font.info.openTypeHheaAscender is not None:
            ascender = str(font.info.openTypeHheaAscender)
        else:
            ascender = ''
        self.ascenderEdit = QLineEdit(ascender, self)
        self.ascenderEdit.setValidator(QIntValidator(self))

        descenderLabel = QLabel("Descender:", self)
        if font.info.openTypeHheaDescender is not None:
            descender = str(font.info.openTypeHheaDescender)
        else:
            descender = ''
        self.descenderEdit = QLineEdit(descender, self)
        self.descenderEdit.setValidator(QIntValidator(self))

        lineGapLabel = QLabel("LineGap:", self)
        if font.info.openTypeHheaLineGap is not None:
            lineGap = str(font.info.openTypeHheaLineGap)
        else:
            lineGap = ''
        self.lineGapEdit = QLineEdit(lineGap, self)
        self.lineGapEdit.setValidator(QIntValidator(self))

        caretSlopeRiseLabel = QLabel("caretSlopeRise:", self)
        if font.info.openTypeHheaCaretSlopeRise is not None:
            caretSlopeRise = str(font.info.openTypeHheaCaretSlopeRise)
        else:
            caretSlopeRise = ''
        self.caretSlopeRiseEdit = QLineEdit(caretSlopeRise, self)
        self.caretSlopeRiseEdit.setValidator(QIntValidator(self))

        caretSlopeRunLabel = QLabel("caretSlopeRun:", self)
        if font.info.openTypeHheaCaretSlopeRun is not None:
            caretSlopeRun = str(font.info.openTypeHheaCaretSlopeRun)
        else:
            caretSlopeRun = ''
        self.caretSlopeRunEdit = QLineEdit(caretSlopeRun, self)
        self.caretSlopeRunEdit.setValidator(QIntValidator(self))

        caretOffsetLabel = QLabel("caretOffset:", self)
        if font.info.openTypeHheaCaretOffset is not None:
            caretOffset = str(font.info.openTypeHheaCaretOffset)
        else:
            caretOffset = ''
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
        # vheaGroup.setFlat(True)
        vheaLayout = QGridLayout(self)

        vertTypoAscenderLabel = QLabel("vertTypoAscender:", self)
        if font.info.openTypeVheaVertTypoAscender is not None:
            vertTypoAscender = str(font.info.openTypeVheaVertTypoAscender)
        else:
            vertTypoAscender = ''
        self.vertTypoAscenderEdit = QLineEdit(vertTypoAscender, self)
        self.vertTypoAscenderEdit.setValidator(QIntValidator(self))

        vertTypoDescenderLabel = QLabel("vertTypoDescender:", self)
        if font.info.openTypeVheaVertTypoDescender is not None:
            vertTypoDescender = str(font.info.openTypeVheaVertTypoDescender)
        else:
            vertTypoDescender = ''
        self.vertTypoDescenderEdit = QLineEdit(vertTypoDescender, self)
        self.vertTypoDescenderEdit.setValidator(QIntValidator(self))

        vertTypoLineGapLabel = QLabel("vertTypoLineGap:", self)
        if font.info.openTypeVheaVertTypoLineGap is not None:
            vertTypoLineGap = str(font.info.openTypeVheaVertTypoLineGap)
        else:
            vertTypoLineGap = ''
        self.vertTypoLineGapEdit = QLineEdit(vertTypoLineGap, self)
        self.vertTypoLineGapEdit.setValidator(QIntValidator(self))

        vheaCaretSlopeRiseLabel = QLabel("caretSlopeRise:", self)
        if font.info.openTypeVheaCaretSlopeRise is not None:
            vheaCaretSlopeRise = str(font.info.openTypeVheaCaretSlopeRise)
        else:
            vheaCaretSlopeRise = ''
        self.vheaCaretSlopeRiseEdit = QLineEdit(vheaCaretSlopeRise, self)
        self.vheaCaretSlopeRiseEdit.setValidator(QIntValidator(self))

        vheaCaretSlopeRunLabel = QLabel("caretSlopeRun:", self)
        if font.info.openTypeVheaCaretSlopeRun is not None:
            vheaCaretSlopeRun = str(font.info.openTypeVheaCaretSlopeRun)
        else:
            vheaCaretSlopeRun = ''
        self.vheaCaretSlopeRunEdit = QLineEdit(vheaCaretSlopeRun, self)
        self.vheaCaretSlopeRunEdit.setValidator(QIntValidator(self))

        vheaCaretOffsetLabel = QLabel("caretOffset:", self)
        if font.info.openTypeVheaCaretOffset is not None:
            vheaCaretOffset = str(font.info.openTypeVheaCaretOffset)
        else:
            vheaCaretOffset = ''
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
        if preferredFamilyName != '':
            font.info.openTypeNamePreferredFamilyName = preferredFamilyName
        else:
            font.info.openTypeNamePreferredFamilyName = None
        preferredSubfamilyName = self.preferredSubfamilyNameEdit.text()
        if preferredSubfamilyName != '':
            font.info.openTypeNamePreferredSubfamilyName = \
                preferredSubfamilyName
        else:
            font.info.openTypeNamePreferredSubfamilyName = None
        WWSFamilyName = self.WWSFamilyNameEdit.text()
        if WWSFamilyName != '':
            font.info.openTypeNameWWSFamilyName = WWSFamilyName
        else:
            font.info.openTypeNameWWSFamilyName = None
        WWSSubfamilyName = self.WWSSubfamilyNameEdit.text()
        if WWSSubfamilyName != '':
            font.info.openTypeNameWWSSubfamilyName = WWSSubfamilyName
        else:
            font.info.openTypeNameWWSSubfamilyName = None
        compatibleFullName = self.compatibleFullNameEdit.text()
        if compatibleFullName != '':
            font.info.openTypeNameCompatibleFullName = compatibleFullName
        else:
            font.info.openTypeNameCompatibleFullName = None
        version = self.versionEdit.text()
        if version != '':
            font.info.openTypeNameVersion = version
        else:
            font.info.openTypeNameVersion = None
        uniqueID = self.uniqueIDEdit.text()
        if uniqueID != '':
            font.info.openTypeNameUniqueID = uniqueID
        else:
            font.info.openTypeNameUniqueID = None
        description = self.descriptionEdit.text()
        if description != '':
            font.info.openTypeNameDescription = description
        else:
            font.info.openTypeNameDescription = None
        sampleText = self.sampleTextEdit.text()
        if sampleText != '':
            font.info.openTypeNameSampleText = sampleText
        else:
            font.info.openTypeNameSampleText = None
        ascender = self.ascenderEdit.text()
        if ascender != '':
            font.info.openTypeHheaAscender = int(ascender)
        else:
            font.info.openTypeHheaAscender = None
        descender = self.descenderEdit.text()
        if descender != '':
            font.info.openTypeHheaDescender = int(descender)
        else:
            font.info.openTypeHheaDescender = None
        lineGap = self.lineGapEdit.text()
        if lineGap != '':
            font.info.openTypeHheaLineGap = int(lineGap)
        else:
            font.info.openTypeHheaLineGap = None
        caretSlopeRise = self.caretSlopeRiseEdit.text()
        if caretSlopeRise != '':
            font.info.openTypeHheaCaretSlopeRise = int(caretSlopeRise)
        else:
            font.info.openTypeHheaCaretSlopeRise = None
        caretSlopeRun = self.caretSlopeRunEdit.text()
        if caretSlopeRun != '':
            font.info.openTypeHheaCaretSlopeRun = int(caretSlopeRun)
        else:
            font.info.openTypeHheaCaretSlopeRun = None
        caretOffset = self.caretOffsetEdit.text()
        if caretOffset != '':
            font.info.openTypeHheaCaretOffset = int(caretOffset)
        else:
            font.info.openTypeHheaCaretOffset = None
        vertTypoAscender = self.vertTypoAscenderEdit.text()
        if vertTypoAscender != '':
            font.info.openTypeVheaAscender = int(vertTypoAscender)
        else:
            font.info.openTypeVheaAscender = None
        vertTypoDescender = self.vertTypoDescenderEdit.text()
        if vertTypoDescender != '':
            font.info.openTypeVheaDescender = int(vertTypoDescender)
        else:
            font.info.openTypeVheaDescender = None
        vertTypoLineGap = self.vertTypoLineGapEdit.text()
        if vertTypoLineGap != '':
            font.info.openTypeVheaLineGap = int(vertTypoLineGap)
        else:
            font.info.openTypeVheaLineGap = None
        vheaCaretSlopeRise = self.vheaCaretSlopeRiseEdit.text()
        if vheaCaretSlopeRise != '':
            font.info.openTypeVheaCaretSlopeRise = int(vheaCaretSlopeRise)
        else:
            font.info.openTypeVheaCaretSlopeRise = None
        vheaCaretSlopeRun = self.vheaCaretSlopeRunEdit.text()
        if vheaCaretSlopeRun != '':
            font.info.openTypeVheaCaretSlopeRun = int(vheaCaretSlopeRun)
        else:
            font.info.openTypeVheaCaretSlopeRun = None
        vheaCaretOffset = self.vheaCaretOffsetEdit.text()
        if vheaCaretOffset != '':
            font.info.openTypeVheaCaretOffset = int(vheaCaretOffset)
        else:
            font.info.openTypeVheaCaretOffset = None


class OS2Tab(QWidget):
    name = "OS/2"

    def __init__(self, font, parent=None):
        super(OS2Tab, self).__init__(parent)

        # OS2Group = QGroupBox("OS/2 table", self)
        # OS2Group.setFlat(True)
        OS2Layout = QGridLayout(self)

        usWidthClassLabel = QLabel("usWidthClass:", self)
        self.usWidthClassDrop = QComboBox(self)
        items = [
            "None", "Ultra-condensed", "Extra-condensed", "Condensed",
            "Semi-Condensed", "Medium (normal)", "Semi-expanded", "Expanded",
            "Extra-expanded", "Ultra-expanded"]
        self.usWidthClassDrop.insertItems(0, items)
        if font.info.openTypeOS2WidthClass is not None:
            self.usWidthClassDrop.setCurrentIndex(
                font.info.openTypeOS2WidthClass)

        usWeightClassLabel = QLabel("usWeightClass:", self)
        if font.info.openTypeOS2WeightClass is not None:
            usWeightClass = str(font.info.openTypeOS2WeightClass)
        else:
            usWeightClass = ''
        self.usWeightClassEdit = QLineEdit(usWeightClass, self)
        positiveValidator = QIntValidator(self)
        positiveValidator.setBottom(0)
        self.usWeightClassEdit.setValidator(positiveValidator)

        fsSelectionLabel = QLabel("fsSelection:", self)
        fsSelection = font.info.openTypeOS2Selection
        self.fsSelectionList = QListView(self)
        items = [
            "1 UNDERSCORE", "2 NEGATIVE", "3 OUTLINED", "4 STRIKEOUT",
            "7 USE_TYPO_METRICS", "8 WWS", "9 OBLIQUE"]
        # http://stackoverflow.com/a/26613163
        model = QStandardItemModel(7, 1)
        for index, elem in enumerate(items):
            item = QStandardItem()
            item.setText(elem)
            item.setCheckable(True)
            bit = index + 1
            if fsSelection is not None and bit in fsSelection:
                # maybe default setting? if so, unneeded
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            model.setItem(index, item)
        self.fsSelectionList.setModel(model)

        achVendorIDLabel = QLabel("achVendorID:", self)
        self.achVendorIDEdit = QLineEdit(font.info.openTypeOS2VendorID, self)
        self.achVendorIDEdit.setMaxLength(4)

        fsTypeLabel = QLabel("fsType:", self)
        fsType = font.info.openTypeOS2Type
        self.fsTypeDrop = QComboBox(self)
        items = [
            "No embedding restrictions", "Restricted embedding",
            "Preview and print embedding allowed",
            "Editable embedding allowed"]
        self.allowSubsettingBox = QCheckBox("Allow subsetting", self)
        self.allowBitmapEmbeddingBox = QCheckBox(
            "Allow only bitmap embedding", self)
        self.fsTypeDrop.currentIndexChanged[int].connect(
            self._updateFsTypeVisibility)
        self.fsTypeDrop.insertItems(0, items)
        if fsType is not None:
            for i in range(1, 4):
                if i in fsType:
                    self.fsTypeDrop.setCurrentIndex(i)
                    break
            self.allowSubsettingBox.setChecked(8 not in fsType)
            self.allowBitmapEmbeddingBox.setChecked(9 in fsType)

        # XXX: ulUnicodeRange

        # XXX: ulCodePageRange

        sTypoAscenderLabel = QLabel("sTypoAscender:", self)
        if font.info.openTypeOS2TypoAscender is not None:
            sTypoAscender = str(font.info.openTypeOS2TypoAscender)
        else:
            sTypoAscender = ''
        self.sTypoAscenderEdit = QLineEdit(sTypoAscender, self)
        self.sTypoAscenderEdit.setValidator(QIntValidator(self))

        sTypoDescenderLabel = QLabel("sTypoDescender:", self)
        if font.info.openTypeOS2TypoDescender is not None:
            sTypoDescender = str(font.info.openTypeOS2TypoDescender)
        else:
            sTypoDescender = ''
        self.sTypoDescenderEdit = QLineEdit(sTypoDescender, self)
        negativeValidator = QIntValidator(self)
        negativeValidator.setTop(0)
        self.sTypoDescenderEdit.setValidator(negativeValidator)

        sTypoLineGapLabel = QLabel("sTypoLineGap:", self)
        if font.info.openTypeOS2TypoLineGap is not None:
            sTypoLineGap = str(font.info.openTypeOS2TypoLineGap)
        else:
            sTypoLineGap = ''
        self.sTypoLineGapEdit = QLineEdit(sTypoLineGap, self)
        self.sTypoLineGapEdit.setValidator(QIntValidator(self))

        usWinAscentLabel = QLabel("usWinAscent:", self)
        if font.info.openTypeOS2WinAscent is not None:
            usWinAscent = str(font.info.openTypeOS2WinAscent)
        else:
            usWinAscent = ''
        self.usWinAscentEdit = QLineEdit(usWinAscent, self)
        self.usWinAscentEdit.setValidator(QIntValidator(self))

        usWinDescentLabel = QLabel("usWinDescent:", self)
        if font.info.openTypeOS2WinDescent is not None:
            usWinDescent = str(font.info.openTypeOS2WinDescent)
        else:
            usWinDescent = ''
        self.usWinDescentEdit = QLineEdit(usWinDescent, self)
        positiveValidator = QIntValidator(self)
        positiveValidator.setBottom(0)
        self.usWinDescentEdit.setValidator(positiveValidator)

        ySubscriptXSizeLabel = QLabel("ySubscriptXSize:", self)
        if font.info.openTypeOS2SubscriptXSize is not None:
            ySubscriptXSize = str(font.info.openTypeOS2SubscriptXSize)
        else:
            ySubscriptXSize = ''
        self.ySubscriptXSizeEdit = QLineEdit(ySubscriptXSize, self)
        self.ySubscriptXSizeEdit.setValidator(QIntValidator(self))

        ySubscriptYSizeLabel = QLabel("ySubscriptYSize:", self)
        if font.info.openTypeOS2SubscriptYSize is not None:
            ySubscriptYSize = str(font.info.openTypeOS2SubscriptYSize)
        else:
            ySubscriptYSize = ''
        self.ySubscriptYSizeEdit = QLineEdit(ySubscriptYSize, self)
        self.ySubscriptYSizeEdit.setValidator(QIntValidator(self))

        ySubscriptXOffsetLabel = QLabel("ySubscriptXOffset:", self)
        if font.info.openTypeOS2SubscriptXOffset is not None:
            ySubscriptXOffset = str(font.info.openTypeOS2SubscriptXOffset)
        else:
            ySubscriptXOffset = ''
        self.ySubscriptXOffsetEdit = QLineEdit(ySubscriptXOffset, self)
        self.ySubscriptXOffsetEdit.setValidator(QIntValidator(self))

        ySubscriptYOffsetLabel = QLabel("ySubscriptYOffset:", self)
        if font.info.openTypeOS2SubscriptYOffset is not None:
            ySubscriptYOffset = str(font.info.openTypeOS2SubscriptYOffset)
        else:
            ySubscriptYOffset = ''
        self.ySubscriptYOffsetEdit = QLineEdit(ySubscriptYOffset, self)
        self.ySubscriptYOffsetEdit.setValidator(QIntValidator(self))

        ySuperscriptXSizeLabel = QLabel("ySuperscriptXSize:", self)
        if font.info.openTypeOS2SuperscriptXSize is not None:
            ySuperscriptXSize = str(font.info.openTypeOS2SuperscriptXSize)
        else:
            ySuperscriptXSize = ''
        self.ySuperscriptXSizeEdit = QLineEdit(ySuperscriptXSize, self)
        self.ySuperscriptXSizeEdit.setValidator(QIntValidator(self))

        ySuperscriptYSizeLabel = QLabel("ySuperscriptYSize:", self)
        if font.info.openTypeOS2SuperscriptYSize is not None:
            ySuperscriptYSize = str(font.info.openTypeOS2SuperscriptYSize)
        else:
            ySuperscriptYSize = ''
        self.ySuperscriptYSizeEdit = QLineEdit(ySuperscriptYSize, self)
        self.ySuperscriptYSizeEdit.setValidator(QIntValidator(self))

        ySuperscriptXOffsetLabel = QLabel("ySuperscriptXOffset:", self)
        if font.info.openTypeOS2SuperscriptXOffset is not None:
            ySuperscriptXOffset = str(font.info.openTypeOS2SuperscriptXOffset)
        else:
            ySuperscriptXOffset = ''
        self.ySuperscriptXOffsetEdit = QLineEdit(ySuperscriptXOffset, self)
        self.ySuperscriptXOffsetEdit.setValidator(QIntValidator(self))

        ySuperscriptYOffsetLabel = QLabel("ySuperscriptYOffset:", self)
        if font.info.openTypeOS2SuperscriptYOffset is not None:
            ySuperscriptYOffset = str(font.info.openTypeOS2SuperscriptYOffset)
        else:
            ySuperscriptYOffset = ''
        self.ySuperscriptYOffsetEdit = QLineEdit(ySuperscriptYOffset, self)
        self.ySuperscriptYOffsetEdit.setValidator(QIntValidator(self))

        yStrikeoutSizeLabel = QLabel("yStrikeoutSize:", self)
        if font.info.openTypeOS2StrikeoutSize is not None:
            yStrikeoutSize = str(font.info.openTypeOS2StrikeoutSize)
        else:
            yStrikeoutSize = ''
        self.yStrikeoutSizeEdit = QLineEdit(yStrikeoutSize, self)
        self.yStrikeoutSizeEdit.setValidator(QIntValidator(self))

        yStrikeoutPositionLabel = QLabel("yStrikeoutPosition:", self)
        if font.info.openTypeOS2StrikeoutPosition is not None:
            yStrikeoutPosition = str(font.info.openTypeOS2StrikeoutPosition)
        else:
            yStrikeoutPosition = ''
        self.yStrikeoutPositionEdit = QLineEdit(yStrikeoutPosition, self)
        self.yStrikeoutPositionEdit.setValidator(QIntValidator(self))

        # XXX: panose

        l = 0
        OS2Layout.addWidget(usWidthClassLabel, l, 0)
        OS2Layout.addWidget(self.usWidthClassDrop, l, 1, 1, 2)
        OS2Layout.addWidget(achVendorIDLabel, l, 3)
        OS2Layout.addWidget(self.achVendorIDEdit, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(usWeightClassLabel, l, 0)
        OS2Layout.addWidget(self.usWeightClassEdit, l, 1, 1, 2)
        l += 1
        OS2Layout.addWidget(fsSelectionLabel, l, 0, 3, 1)
        OS2Layout.addWidget(self.fsSelectionList, l, 1, 3, 2)
        OS2Layout.addWidget(fsTypeLabel, l, 3, 3, 1)
        OS2Layout.addWidget(self.fsTypeDrop, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(self.allowSubsettingBox, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(self.allowBitmapEmbeddingBox, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(sTypoAscenderLabel, l, 0)
        OS2Layout.addWidget(self.sTypoAscenderEdit, l, 1, 1, 2)
        OS2Layout.addWidget(usWinAscentLabel, l, 3)
        OS2Layout.addWidget(self.usWinAscentEdit, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(sTypoDescenderLabel, l, 0)
        OS2Layout.addWidget(self.sTypoDescenderEdit, l, 1, 1, 2)
        OS2Layout.addWidget(usWinDescentLabel, l, 3)
        OS2Layout.addWidget(self.usWinDescentEdit, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(sTypoLineGapLabel, l, 0)
        OS2Layout.addWidget(self.sTypoLineGapEdit, l, 1, 1, 2)
        l += 1
        OS2Layout.addWidget(ySubscriptXSizeLabel, l, 0)
        OS2Layout.addWidget(self.ySubscriptXSizeEdit, l, 1, 1, 2)
        OS2Layout.addWidget(ySubscriptXOffsetLabel, l, 3)
        OS2Layout.addWidget(self.ySubscriptXOffsetEdit, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(ySubscriptYSizeLabel, l, 0)
        OS2Layout.addWidget(self.ySubscriptYSizeEdit, l, 1, 1, 2)
        OS2Layout.addWidget(ySubscriptYOffsetLabel, l, 3)
        OS2Layout.addWidget(self.ySubscriptYOffsetEdit, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(ySuperscriptXSizeLabel, l, 0)
        OS2Layout.addWidget(self.ySuperscriptXSizeEdit, l, 1, 1, 2)
        OS2Layout.addWidget(ySuperscriptXOffsetLabel, l, 3)
        OS2Layout.addWidget(self.ySuperscriptXOffsetEdit, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(ySuperscriptYSizeLabel, l, 0)
        OS2Layout.addWidget(self.ySuperscriptYSizeEdit, l, 1, 1, 2)
        OS2Layout.addWidget(ySuperscriptYOffsetLabel, l, 3)
        OS2Layout.addWidget(self.ySuperscriptYOffsetEdit, l, 4, 1, 2)
        l += 1
        OS2Layout.addWidget(yStrikeoutSizeLabel, l, 0)
        OS2Layout.addWidget(self.yStrikeoutSizeEdit, l, 1, 1, 2)
        OS2Layout.addWidget(yStrikeoutPositionLabel, l, 3)
        OS2Layout.addWidget(self.yStrikeoutPositionEdit, l, 4, 1, 2)
        # OS2Group.setLayout(OS2Layout)
        self.setLayout(OS2Layout)

    def _updateFsTypeVisibility(self, index):
        if index == 0:
            # TODO: maybe uncheck as well?
            self.allowSubsettingBox.setEnabled(False)
            self.allowBitmapEmbeddingBox.setEnabled(False)
        else:
            self.allowSubsettingBox.setEnabled(True)
            self.allowBitmapEmbeddingBox.setEnabled(True)

    def writeValues(self, font):
        usWidthClass = self.usWidthClassDrop.currentIndex()
        if usWidthClass != 0:
            font.info.openTypeOS2WidthClass = usWidthClass
        else:
            font.info.openTypeOS2WidthClass = None
        usWeightClass = self.usWeightClassEdit.text()
        if usWeightClass != '':
            font.info.openTypeOS2WeightClass = int(usWeightClass)
        else:
            font.info.openTypeOS2WeightClass = None

        fsSelectionModel = self.fsSelectionList.model()
        fsSelection = []
        for i in range(7):
            item = fsSelectionModel.item(i)
            if item.checkState() == Qt.Checked:
                fsSelection.append(i)
        if len(fsSelection):
            font.info.openTypeOS2Selection = fsSelection
        else:
            # XXX: None or empty array? should distinct those cases
            font.info.openTypeOS2Selection = None

        fsTypeIndex = self.fsTypeDrop.currentIndex()
        fsType = []
        if fsTypeIndex > 0:
            fsType.append(fsTypeIndex)
            if not self.allowSubsettingBox.isChecked():
                fsType.append(8)
            if self.allowBitmapEmbeddingBox.isChecked():
                fsType.append(9)
        # TODO: provide a way to represent None w this?
        font.info.openTypeOS2Type = fsType

        # TODO: see if data needs to be padded to 4 chars.
        # I think that this is to be deferred to ufo2fdk(?)
        font.info.openTypeOS2VendorID = self.achVendorIDEdit.text()

        # XXX: ulUnicodeRange

        # XXX: ulCodePageRange

        sTypoAscender = self.sTypoAscenderEdit.text()
        if sTypoAscender != '':
            font.info.openTypeOS2TypoAscender = int(sTypoAscender)
        else:
            font.info.openTypeOS2TypoAscender = None
        sTypoDescender = self.sTypoDescenderEdit.text()
        if sTypoDescender != '':
            font.info.openTypeOS2TypoDescender = int(sTypoDescender)
        else:
            font.info.openTypeOS2TypoDescender = None
        sTypoLineGap = self.sTypoLineGapEdit.text()
        if sTypoLineGap != '':
            font.info.openTypeOS2TypoLineGap = int(sTypoLineGap)
        else:
            font.info.openTypeOS2TypoLineGap = None

        usWinAscent = self.usWinAscentEdit.text()
        if usWinAscent != '':
            font.info.openTypeOS2WinAscent = int(usWinAscent)
        else:
            font.info.openTypeOS2WinAscent = None
        usWinDescent = self.usWinDescentEdit.text()
        if usWinDescent != '':
            font.info.openTypeOS2WinDescent = int(usWinDescent)
        else:
            font.info.openTypeOS2WinDescent = None

        ySubscriptXSize = self.ySubscriptXSizeEdit.text()
        if ySubscriptXSize != '':
            font.info.openTypeOS2SubscriptXSize = int(ySubscriptXSize)
        else:
            font.info.openTypeOS2SubscriptXSize = None
        ySubscriptYSize = self.ySubscriptYSizeEdit.text()
        if ySubscriptYSize != '':
            font.info.openTypeOS2SubscriptYSize = int(ySubscriptYSize)
        else:
            font.info.openTypeOS2SubscriptYSize = None
        ySubscriptXOffset = self.ySubscriptXOffsetEdit.text()
        if ySubscriptXOffset != '':
            font.info.openTypeOS2SubscriptXOffset = int(ySubscriptXOffset)
        else:
            font.info.openTypeOS2SubscriptXOffset = None
        ySubscriptYOffset = self.ySubscriptYOffsetEdit.text()
        if ySubscriptYOffset != '':
            font.info.openTypeOS2SubscriptYOffset = int(ySubscriptYOffset)
        else:
            font.info.openTypeOS2SubscriptYOffset = None

        ySuperscriptXSize = self.ySuperscriptXSizeEdit.text()
        if ySuperscriptXSize != '':
            font.info.openTypeOS2SuperscriptXSize = int(ySuperscriptXSize)
        else:
            font.info.openTypeOS2SuperscriptXSize = None
        ySuperscriptYSize = self.ySuperscriptYSizeEdit.text()
        if ySuperscriptYSize != '':
            font.info.openTypeOS2SuperscriptYSize = int(ySuperscriptYSize)
        else:
            font.info.openTypeOS2SuperscriptYSize = None
        ySuperscriptXOffset = self.ySuperscriptXOffsetEdit.text()
        if ySuperscriptXOffset != '':
            font.info.openTypeOS2SuperscriptXOffset = int(ySuperscriptXOffset)
        else:
            font.info.openTypeOS2SuperscriptXOffset = None
        ySuperscriptYOffset = self.ySuperscriptYOffsetEdit.text()
        if ySuperscriptYOffset != '':
            font.info.openTypeOS2SuperscriptYOffset = int(ySuperscriptYOffset)
        else:
            font.info.openTypeOS2SuperscriptYOffset = None

        yStrikeoutSize = self.yStrikeoutSizeEdit.text()
        if yStrikeoutSize != '':
            font.info.openTypeOS2StrikeoutSize = int(yStrikeoutSize)
        else:
            font.info.openTypeOS2StrikeoutSize = None
        yStrikeoutPosition = self.yStrikeoutPositionEdit.text()
        if yStrikeoutPosition != '':
            font.info.openTypeOS2StrikeoutPosition = int(yStrikeoutPosition)
        else:
            font.info.openTypeOS2StrikeoutPosition = None

        # XXX: panose


class PostScriptTab(QWidget):
    name = "Postscript"

    def __init__(self, font, parent=None):
        super(PostScriptTab, self).__init__(parent)

        namingGroup = QGroupBox("Naming", self)
        # namingGroup.setFlat(True)
        namingLayout = QGridLayout(self)

        fontNameLabel = QLabel("FontName:", self)
        self.fontNameEdit = QLineEdit(font.info.postscriptFontName, self)

        fullNameLabel = QLabel("FullName:", self)
        self.fullNameEdit = QLineEdit(font.info.postscriptFullName, self)

        weightNameLabel = QLabel("WeightName:", self)
        self.weightNameEdit = QLineEdit(font.info.postscriptWeightName, self)

        uniqueIDLabel = QLabel("Unique ID:", self)
        if font.info.postscriptUniqueID is not None:
            uniqueID = str(font.info.postscriptUniqueID)
        else:
            uniqueID = ''
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
        # hintingGroup.setFlat(True)
        hintingLayout = QGridLayout(self)

        blueValuesLabel = QLabel("Blue values:", self)
        blueValues = " ".join(str(val)
                              for val in font.info.postscriptBlueValues)
        self.blueValuesEdit = QLineEdit(blueValues, self)

        otherBluesLabel = QLabel("Other blues:", self)
        otherBlues = " ".join(str(val)
                              for val in font.info.postscriptOtherBlues)
        self.otherBluesEdit = QLineEdit(otherBlues, self)

        familyBluesLabel = QLabel("Family blues:", self)
        familyBlues = " ".join(str(val)
                               for val in font.info.postscriptFamilyBlues)
        self.familyBluesEdit = QLineEdit(familyBlues, self)

        familyOtherBluesLabel = QLabel("Family other blues:", self)
        familyOtherBlues = " ".join(
            str(val) for val in font.info.postscriptFamilyOtherBlues)
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
        if font.info.postscriptBlueFuzz is not None:
            blueFuzz = str(font.info.postscriptBlueFuzz)
        else:
            blueFuzz = ''
        self.blueFuzzEdit = QLineEdit(blueFuzz, self)
        self.blueFuzzEdit.setValidator(QDoubleValidator(self))

        stemSnapHLabel = QLabel("StemSnapH:", self)
        stemSnapH = " ".join(str(val) for val in font.info.postscriptStemSnapH)
        self.stemSnapHEdit = QLineEdit(stemSnapH, self)

        blueScaleLabel = QLabel("Blue scale:", self)
        if font.info.postscriptBlueScale is not None:
            blueScale = str(font.info.postscriptBlueScale)
        else:
            blueScale = ''
        self.blueScaleEdit = QLineEdit(blueScale, self)
        self.blueScaleEdit.setValidator(QDoubleValidator(self))

        stemSnapVLabel = QLabel("StemSnapV:", self)
        stemSnapV = " ".join(str(val) for val in font.info.postscriptStemSnapV)
        self.stemSnapVEdit = QLineEdit(stemSnapV, self)

        blueShiftLabel = QLabel("Blue shift:", self)
        if font.info.postscriptBlueShift is not None:
            blueShift = str(font.info.postscriptBlueShift)
        else:
            blueShift = ''
        self.blueShiftEdit = QLineEdit(blueShift, self)
        self.blueShiftEdit.setValidator(QDoubleValidator(self))

        forceBoldLabel = QLabel("Force bold:", self)
        forceBold = font.info.postscriptForceBold
        self.forceBoldBox = QCheckBox(self)
        self.forceBoldBox.setTristate()
        if forceBold is None:
            self.forceBoldBox.setCheckState(Qt.PartiallyChecked)
        else:
            self.forceBoldBox.setChecked(forceBold)

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
        # metricsGroup.setFlat(True)
        metricsLayout = QGridLayout(self)

        defaultWidthXLabel = QLabel("DefaultWidthX:", self)
        if font.info.postscriptDefaultWidthX is not None:
            defaultWidthX = str(font.info.postscriptDefaultWidthX)
        else:
            defaultWidthX = ''
        self.defaultWidthXEdit = QLineEdit(defaultWidthX, self)
        self.defaultWidthXEdit.setValidator(QDoubleValidator(self))

        underlineThicknessLabel = QLabel("UnderlineThickness:", self)
        if font.info.postscriptUnderlineThickness is not None:
            underlineThickness = str(font.info.postscriptUnderlineThickness)
        else:
            underlineThickness = ''
        self.underlineThicknessEdit = QLineEdit(underlineThickness, self)
        self.underlineThicknessEdit.setValidator(QDoubleValidator(self))

        nominalWidthXLabel = QLabel("NominalWidthX:", self)
        if font.info.postscriptNominalWidthX is not None:
            nominalWidthX = str(font.info.postscriptNominalWidthX)
        else:
            nominalWidthX = ''
        self.nominalWidthXEdit = QLineEdit(nominalWidthX, self)
        self.nominalWidthXEdit.setValidator(QDoubleValidator(self))

        underlinePositionLabel = QLabel("UnderlinePosition:", self)
        if font.info.postscriptUnderlinePosition is not None:
            underlinePosition = str(font.info.postscriptUnderlinePosition)
        else:
            underlinePosition = ''
        self.underlinePositionEdit = QLineEdit(underlinePosition, self)
        self.underlinePositionEdit.setValidator(QDoubleValidator(self))

        slantAngleLabel = QLabel("SlantAngle:", self)
        if font.info.postscriptSlantAngle is not None:
            slantAngle = str(font.info.postscriptSlantAngle)
        else:
            slantAngle = ''
        self.slantAngleEdit = QLineEdit(slantAngle, self)
        self.slantAngleEdit.setValidator(QDoubleValidator(self))

        isFixedPitchLabel = QLabel("isFixedPitched:", self)
        isFixedPitch = font.info.postscriptIsFixedPitch
        self.isFixedPitchBox = QCheckBox(self)
        self.isFixedPitchBox.setTristate()
        if isFixedPitch is None:
            self.isFixedPitchBox.setCheckState(Qt.PartiallyChecked)
        else:
            self.isFixedPitchBox.setChecked(isFixedPitch)

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
        # charactersGroup.setFlat(True)
        charactersLayout = QGridLayout(self)

        defaultCharacterLabel = QLabel("Default character:", self)
        self.defaultCharacterEdit = QLineEdit(
            font.info.postscriptDefaultCharacter, self)

        windowsCharacterSetLabel = QLabel("Windows character set:", self)
        self.windowsCharacterSetDrop = QComboBox(self)
        items = [
            "None", "ANSI", "Default", "Symbol", "Macintosh", "Shift JIS",
            "Hangul", "Hangul (Johab)", "GB2312", "Chinese BIG5", "Greek",
            "Turkish", "Vietnamese", "Hebrew", "Arabic", "Baltic", "Bitstream",
            "Cyrillic", "Thai", "Eastern European", "OEM"]
        self.windowsCharacterSetDrop.insertItems(0, items)
        if font.info.postscriptWindowsCharacterSet is not None:
            self.windowsCharacterSetDrop.setCurrentIndex(
                font.info.postscriptWindowsCharacterSet)

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
        if fontName != '':
            font.info.postscriptFontName = fontName
        else:
            font.info.postscriptFontName = None
        fullName = self.fullNameEdit.text()
        if fullName != '':
            font.info.postscriptFullName = fullName
        else:
            font.info.postscriptFullName = None
        weightName = self.weightNameEdit.text()
        if weightName != '':
            font.info.postscriptWeightName = weightName
        else:
            font.info.postscriptWeightName = None
        uniqueID = self.uniqueIDEdit.text()
        if uniqueID != '':
            font.info.postscriptUniqueID = int(uniqueID)
        else:
            font.info.postscriptUniqueID = None
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
        if "." in blueFuzz:
            font.info.postscriptBlueFuzz = float(blueFuzz)
        elif blueFuzz != '':
            font.info.postscriptBlueFuzz = int(blueFuzz)
        else:
            font.info.postscriptBlueFuzz = None
        blueScale = self.blueScaleEdit.text()
        if blueScale != '':
            font.info.postscriptBlueScale = float(blueScale)
        else:
            font.info.postscriptBlueScale = None
        blueShift = self.blueShiftEdit.text()
        if "." in blueShift:
            font.info.postscriptBlueShift = float(blueShift)
        elif blueShift != '':
            font.info.postscriptBlueShift = int(blueShift)
        else:
            font.info.postscriptBlueShift = None
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
        if "." in defaultWidthX:
            font.info.postscriptDefaultWidthX = float(defaultWidthX)
        elif defaultWidthX != '':
            font.info.postscriptDefaultWidthX = int(defaultWidthX)
        else:
            font.info.postscriptDefaultWidthX = None
        nominalWidthX = self.nominalWidthXEdit.text()
        if "." in nominalWidthX:
            font.info.postscriptNominalWidthX = float(nominalWidthX)
        elif nominalWidthX != '':
            font.info.postscriptNominalWidthX = int(nominalWidthX)
        else:
            font.info.postscriptNominalWidthX = None
        underlineThickness = self.underlineThicknessEdit.text()
        if "." in underlineThickness:
            font.info.postscriptUnderlineThickness = float(underlineThickness)
        elif underlineThickness != '':
            font.info.postscriptUnderlineThickness = \
                int(underlineThickness)
        else:
            font.info.postscriptUnderlineThickness = None
        underlinePosition = self.underlinePositionEdit.text()
        if "." in underlinePosition:
            font.info.postscriptUnderlinePosition = float(underlinePosition)
        elif underlinePosition != '':
            font.info.postscriptUnderlinePosition = int(underlinePosition)
        else:
            font.info.postscriptUnderlinePosition = None
        slantAngle = self.slantAngleEdit.text()
        if "." in slantAngle:
            font.info.postscriptSlantAngle = float(slantAngle)
        elif slantAngle != '':
            font.info.postscriptSlantAngle = int(slantAngle)
        else:
                font.info.postscriptSlantAngle = None
        isFixedPitch = self.isFixedPitchBox.checkState()
        if isFixedPitch == Qt.PartiallyChecked:
            font.info.postscriptIsFixedPitch = None
        else:
            font.info.postscriptIsFixedPitch = bool(isFixedPitch)
        defaultCharacter = self.defaultCharacterEdit.text()
        if defaultCharacter != '':
            font.info.postscriptDefaultCharacter = defaultCharacter
        else:
            font.info.postscriptDefaultCharacter = None
        windowsCharacterSet = self.windowsCharacterSetDrop.currentIndex()
        if windowsCharacterSet == 0:
            font.info.postscriptWindowsCharacterSet = None
        else:
            font.info.postscriptWindowsCharacterSet = windowsCharacterSet
