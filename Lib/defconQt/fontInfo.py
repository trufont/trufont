from PyQt5.QtCore import QDate, QDateTime, QRegularExpression, QTime, Qt
from PyQt5.QtGui import (
    QDoubleValidator, QIntValidator, QRegularExpressionValidator,
    QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox,
    QGridLayout, QGroupBox, QLabel, QLineEdit, QListView, QPlainTextEdit,
    QTabWidget, QVBoxLayout, QWidget)


class InfoTabWidget(QTabWidget):

    def addNamedTab(self, tab):
        self.addTab(tab, tab.name)


class TabDialog(QDialog):

    def __init__(self, font, parent=None):
        super().__init__(parent)
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
        super().accept()


class TabWidget(QWidget):

    def __init__(self, font, parent=None, name=None):
        self.name = name
        self.font = font
        super().__init__(parent)

    def loadString(self, font, src, dst):
        value = getattr(font.info, src)
        if value is not None:
            setattr(self, dst + "Edit", QLineEdit(value, self))
        else:
            setattr(self, dst + "Edit", QLineEdit(None, self))

    def writeString(self, font, src, dst):
        value = getattr(self, src + "Edit").text()
        if value != "":
            setattr(font.info, dst, value)
        else:
            setattr(font.info, dst, None)

    def loadMultilineString(self, font, src, dst):
        value = getattr(font.info, src)
        if value is not None:
            setattr(self, dst + "Edit", QPlainTextEdit(value, self))
        else:
            setattr(self, dst + "Edit", QPlainTextEdit(None, self))

    def writeMultilineString(self, font, src, dst):
        value = getattr(self, src + "Edit").toPlainText()
        if value != "":
            setattr(font.info, dst, value)
        else:
            setattr(font.info, dst, None)

    def loadInteger(self, font, src, dst):
        value = getattr(font.info, src)
        if value is not None:
            value = str(value)
        else:
            value = ""
        setattr(self, dst + "Edit", QLineEdit(value, self))
        getattr(self, dst + "Edit").setValidator(QIntValidator(self))

    def writeInteger(self, font, src, dst):
        value = getattr(self, src + "Edit").text()
        if value != "":
            setattr(font.info, dst, int(value))
        else:
            setattr(font.info, dst, None)

    def loadPositiveInteger(self, font, src, dst):
        value = getattr(font.info, src)
        if value is not None:
            value = str(value)
        else:
            value = ""
        setattr(self, dst + "Edit", QLineEdit(value, self))
        validator = QIntValidator(self)
        validator.setBottom(0)
        getattr(self, dst + "Edit").setValidator(validator)

    writePositiveInteger = writeInteger

    def loadIntegerFloat(self, font, src, dst):
        value = getattr(font.info, src)
        if value is not None:
            value = str(value)
        else:
            value = ""
        setattr(self, dst + "Edit", QLineEdit(value, self))
        getattr(self, dst + "Edit").setValidator(QDoubleValidator(self))

    def writeIntegerFloat(self, font, src, dst):
        value = getattr(self, src + "Edit").text()
        if "." in value:
            setattr(font.info, dst, float(value))
        elif value:
            setattr(font.info, dst, int(value))
        else:
            setattr(font.info, dst, None)

    def loadPositiveIntegerFloat(self, font, src, dst):
        value = getattr(font.info, src)
        if value is not None:
            value = str(value)
        else:
            value = ""
        setattr(self, dst + "Edit", QLineEdit(value, self))
        validator = QDoubleValidator(self)
        validator.setBottom(0)
        getattr(self, dst + "Edit").setValidator(validator)

    writePositiveIntegerFloat = writeIntegerFloat

    def loadIntegerFloatList(self, font, src, dst):
        values = " ".join(str(val) for val in getattr(font.info, src))
        setattr(self, dst + "Edit", QLineEdit(values, self))
        validator = QRegularExpressionValidator(self)
        validator.setRegularExpression(
            QRegularExpression("(-?\d+(.\d+)?\s*)*"))
        getattr(self, dst + "Edit").setValidator(validator)

    def writeIntegerFloatList(self, font, src, dst):
        values = getattr(self, src + "Edit").text().split()
        dstValues = []
        for val in values:
            if "." in val:
                dstValues.append(float(val))
            elif val not in ("", " "):
                dstValues.append(int(val))
        setattr(font.info, dst, dstValues)

    def loadBoolean(self, font, src, dst):
        value = getattr(font.info, src)
        setattr(self, dst + "Box", QCheckBox(self))
        if value is None:
            getattr(self, dst + "Box").setCheckState(Qt.PartiallyChecked)
        else:
            getattr(self, dst + "Box").setCheckState(value)

    def writeBoolean(self, font, src, dst):
        value = getattr(self, src + "Box").checkState()
        if value == Qt.PartiallyChecked:
            setattr(font.info, dst, None)
        else:
            setattr(font.info, dst, bool(value))


class GeneralTab(TabWidget):

    def __init__(self, font, parent=None):
        super().__init__(parent, name="General")
        mainLayout = QGridLayout(self)

        familyNameLabel = QLabel("Family name:", self)
        styleNameLabel = QLabel("Style name:", self)
        designerLabel = QLabel("Designer:", self)
        designerURLLabel = QLabel("Designer URL:", self)
        manufacturerLabel = QLabel("Manufacturer:", self)
        manufacturerURLLabel = QLabel("Manufacturer URL:", self)
        copyrightLabel = QLabel("Copyright:", self)
        licenseLabel = QLabel("License:", self)
        licenseURLLabel = QLabel("License URL:", self)
        trademarkLabel = QLabel("Trademark:", self)
        # TODO: give visual feedback of input data validity using QLineEdit
        # lose focus event
        # http://snorf.net/blog/2014/08/09/using-qvalidator-in-pyqt4-to-validate-user-input/ # noqa
        versionLabel = QLabel("Version:", self)
        versionDotLabel = QLabel(".", self)
        self.loadString(font, "familyName", "familyName")
        self.loadString(font, "styleName", "styleName")
        self.loadString(font, "openTypeNameDesigner", "designer")
        self.loadString(font, "openTypeNameDesignerURL", "designerURL")
        self.loadString(font, "openTypeNameManufacturer", "manufacturer")
        self.loadString(font, "openTypeNameManufacturerURL", "manufacturerURL")
        self.loadMultilineString(font, "copyright", "copyright")
        self.loadMultilineString(font, "openTypeNameLicense", "license")
        self.loadString(font, "openTypeNameLicenseURL", "licenseURL")
        self.loadString(font, "trademark", "trademark")
        self.loadInteger(font, "versionMajor", "versionMajor")
        self.versionMajorEdit.setAlignment(Qt.AlignRight)
        self.loadPositiveInteger(font, "versionMinor", "versionMinor")

        mainLayout.addWidget(familyNameLabel, 0, 0)
        mainLayout.addWidget(self.familyNameEdit, 0, 1, 1, 3)
        mainLayout.addWidget(styleNameLabel, 0, 4)
        mainLayout.addWidget(self.styleNameEdit, 0, 5)
        mainLayout.addWidget(designerLabel, 1, 0)
        mainLayout.addWidget(self.designerEdit, 1, 1, 1, 5)
        mainLayout.addWidget(designerURLLabel, 2, 0)
        mainLayout.addWidget(self.designerURLEdit, 2, 1, 1, 5)
        mainLayout.addWidget(manufacturerLabel, 3, 0)
        mainLayout.addWidget(self.manufacturerEdit, 3, 1, 1, 5)
        mainLayout.addWidget(manufacturerURLLabel, 4, 0)
        mainLayout.addWidget(self.manufacturerURLEdit, 4, 1, 1, 5)
        mainLayout.addWidget(copyrightLabel, 5, 0)
        mainLayout.addWidget(self.copyrightEdit, 5, 1, 1, 5)
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
        mainLayout.addWidget(licenseLabel, 7, 0)
        mainLayout.addWidget(self.licenseEdit, 7, 1, 1, 5)
        mainLayout.addWidget(licenseURLLabel, 8, 0)
        mainLayout.addWidget(self.licenseURLEdit, 8, 1, 1, 5)
        mainLayout.addWidget(trademarkLabel, 9, 0)
        mainLayout.addWidget(self.trademarkEdit, 9, 1, 1, 5)

        self.setLayout(mainLayout)

    def writeValues(self, font):
        self.writeString(font, "familyName", "familyName")
        self.writeString(font, "styleName", "styleName")
        self.writeString(font, "trademark", "trademark")
        self.writeMultilineString(font, "copyright", "copyright")
        self.writeString(font, "designer", "openTypeNameDesigner")
        self.writeString(font, "designerURL", "openTypeNameDesignerURL")
        self.writeString(font, "manufacturer", "openTypeNameManufacturer")
        self.writeString(
            font, "manufacturerURL", "openTypeNameManufacturerURL")
        self.writeMultilineString(font, "license", "openTypeNameLicense")
        self.writeString(font, "licenseURL", "openTypeNameLicenseURL")

        self.writeInteger(font, "versionMajor", "versionMajor")
        self.writePositiveInteger(font, "versionMinor", "versionMinor")

        font.info.openTypeHeadCreated = \
            self.dateCreatedEdit.dateTime().toString("yyyy/MM/dd hh:mm:ss")


class MetricsTab(TabWidget):

    def __init__(self, font, parent=None):
        super().__init__(parent, name="Metrics")
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
        elif sn == "italic":
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
        ascenderLabel = QLabel("Ascender:", self)
        capHeightLabel = QLabel("Cap height:", self)
        italicAngleLabel = QLabel("Italic angle:", self)
        descenderLabel = QLabel("Descender:", self)
        xHeightLabel = QLabel("x-height:", self)
        noteLabel = QLabel("Note:", self)
        # In the UFO specs these are integer or float, and unitsPerEm is
        # non-negative integer or float
        self.loadPositiveIntegerFloat(font, "unitsPerEm", "unitsPerEm")
        self.loadIntegerFloat(font, "ascender", "ascender")
        self.loadIntegerFloat(font, "capHeight", "capHeight")
        self.loadIntegerFloat(font, "italicAngle", "italicAngle")
        self.loadIntegerFloat(font, "descender", "descender")
        self.loadIntegerFloat(font, "xHeight", "xHeight")
        self.loadMultilineString(font, "note", "note")

        mainLayout.addWidget(unitsPerEmLabel, 1, 0)
        mainLayout.addWidget(self.unitsPerEmEdit, 1, 1)
        mainLayout.addWidget(ascenderLabel, 1, 2)
        mainLayout.addWidget(self.ascenderEdit, 1, 3)
        mainLayout.addWidget(capHeightLabel, 1, 4)
        mainLayout.addWidget(self.capHeightEdit, 1, 5)
        mainLayout.addWidget(italicAngleLabel, 2, 0)
        mainLayout.addWidget(self.italicAngleEdit, 2, 1)
        mainLayout.addWidget(descenderLabel, 2, 2)
        mainLayout.addWidget(self.descenderEdit, 2, 3)
        mainLayout.addWidget(xHeightLabel, 2, 4)
        mainLayout.addWidget(self.xHeightEdit, 2, 5)
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

        self.writePositiveIntegerFloat(font, "unitsPerEm", "unitsPerEm")
        self.writeIntegerFloat(font, "italicAngle", "italicAngle")
        self.writeIntegerFloat(font, "ascender", "ascender")
        self.writeIntegerFloat(font, "descender", "descender")
        self.writeIntegerFloat(font, "capHeight", "capHeight")
        self.writeIntegerFloat(font, "xHeight", "xHeight")

        self.writeMultilineString(font, "note", "note")


class OpenTypeTab(TabWidget):

    def __init__(self, font, parent=None):
        super().__init__(parent, name="OpenType")

        nameGroup = QGroupBox("name table", self)
        # nameGroup.setFlat(True)
        nameLayout = QGridLayout(self)

        preferredFamilyNameLabel = QLabel("Pref. Family Name:", self)
        preferredSubfamilyNameLabel = QLabel("Pref. Subfamily Name:", self)
        compatibleFullNameLabel = QLabel("Compatible Full Name:", self)
        WWSFamilyNameLabel = QLabel("WWS Family Name:", self)
        WWSSubfamilyNameLabel = QLabel("WWS Subfamily Name:", self)
        versionLabel = QLabel("Version:", self)
        uniqueIDLabel = QLabel("Unique ID:", self)
        descriptionLabel = QLabel("Description:", self)
        sampleTextLabel = QLabel("Sample text:", self)
        self.loadString(
            font, "openTypeNamePreferredFamilyName", "preferredFamilyName")
        self.loadString(
            font, "openTypeNamePreferredSubfamilyName",
            "preferredSubfamilyName")
        self.loadString(
            font, "openTypeNameCompatibleFullName", "compatibleFullName")
        self.loadString(font, "openTypeNameWWSFamilyName", "WWSFamilyName")
        self.loadString(
            font, "openTypeNameWWSSubfamilyName", "WWSSubfamilyName")
        self.loadString(font, "openTypeNameVersion", "version")
        self.loadString(font, "openTypeNameUniqueID", "uniqueID")
        self.loadString(font, "openTypeNameDescription", "description")
        self.loadString(font, "openTypeNameSampleText", "sampleText")

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
        descenderLabel = QLabel("Descender:", self)
        lineGapLabel = QLabel("LineGap:", self)
        caretSlopeRiseLabel = QLabel("caretSlopeRise:", self)
        caretSlopeRunLabel = QLabel("caretSlopeRun:", self)
        caretOffsetLabel = QLabel("caretOffset:", self)
        self.loadInteger(font, "openTypeHheaAscender", "ascender")
        self.loadInteger(font, "openTypeHheaDescender", "descender")
        self.loadInteger(font, "openTypeHheaLineGap", "lineGap")
        self.loadInteger(font, "openTypeHheaCaretSlopeRise", "caretSlopeRise")
        self.loadInteger(font, "openTypeHheaCaretSlopeRun", "caretSlopeRun")
        self.loadInteger(font, "openTypeHheaCaretOffset", "caretOffset")

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
        vertTypoDescenderLabel = QLabel("vertTypoDescender:", self)
        vertTypoLineGapLabel = QLabel("vertTypoLineGap:", self)
        vheaCaretSlopeRiseLabel = QLabel("caretSlopeRise:", self)
        vheaCaretSlopeRunLabel = QLabel("caretSlopeRun:", self)
        vheaCaretOffsetLabel = QLabel("caretOffset:", self)
        self.loadInteger(
            font, "openTypeVheaVertTypoAscender", "vertTypoAscender")
        self.loadInteger(
            font, "openTypeVheaVertTypoDescender", "vertTypoDescender")
        self.loadInteger(
            font, "openTypeVheaVertTypoLineGap", "vertTypoLineGap")
        self.loadInteger(
            font, "openTypeVheaCaretSlopeRise", "vheaCaretSlopeRise")
        self.loadInteger(
            font, "openTypeVheaCaretSlopeRun", "vheaCaretSlopeRun")
        self.loadInteger(font, "openTypeVheaCaretOffset", "vheaCaretOffset")

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
        self.writeString(
            font, "preferredFamilyName", "openTypeNamePreferredFamilyName")
        self.writeString(
            font, "preferredSubfamilyName",
            "openTypeNamePreferredSubfamilyName")
        self.writeString(font, "WWSFamilyName", "openTypeNameWWSFamilyName")
        self.writeString(
            font, "WWSSubfamilyName", "openTypeNameWWSSubfamilyName")
        self.writeString(
            font, "compatibleFullName", "openTypeNameCompatibleFullName")
        self.writeString(font, "version", "openTypeNameVersion")
        self.writeString(font, "uniqueID", "openTypeNameUniqueID")
        self.writeString(font, "description", "openTypeNameDescription")
        self.writeString(font, "sampleText", "openTypeNameSampleText")
        self.writeInteger(font, "ascender", "openTypeHheaAscender")
        self.writeInteger(font, "descender", "openTypeHheaDescender")
        self.writeInteger(font, "lineGap", "openTypeHheaLineGap")
        self.writeInteger(font, "caretSlopeRise", "openTypeHheaCaretSlopeRise")
        self.writeInteger(font, "caretSlopeRun", "openTypeHheaCaretSlopeRun")
        self.writeInteger(font, "caretOffset", "openTypeHheaCaretOffset")
        self.writeInteger(
            font, "vertTypoAscender", "openTypeVheaVertTypoAscender")
        self.writeInteger(
            font, "vertTypoDescender", "openTypeVheaVertTypoDescender")
        self.writeInteger(
            font, "vertTypoLineGap", "openTypeVheaVertTypoLineGap")
        self.writeInteger(
            font, "vheaCaretSlopeRise", "openTypeVheaCaretSlopeRise")
        self.writeInteger(
            font, "vheaCaretSlopeRun", "openTypeVheaCaretSlopeRun")
        self.writeInteger(font, "vheaCaretOffset", "openTypeVheaCaretOffset")


class OS2Tab(TabWidget):

    def __init__(self, font, parent=None):
        super().__init__(parent, name="OS/2")

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
        sTypoDescenderLabel = QLabel("sTypoDescender:", self)
        sTypoLineGapLabel = QLabel("sTypoLineGap:", self)
        usWeightClassLabel = QLabel("usWeightClass:", self)
        usWinAscentLabel = QLabel("usWinAscent:", self)
        usWinDescentLabel = QLabel("usWinDescent:", self)
        ySubscriptXSizeLabel = QLabel("ySubscriptXSize:", self)
        ySubscriptYSizeLabel = QLabel("ySubscriptYSize:", self)
        ySubscriptXOffsetLabel = QLabel("ySubscriptXOffset:", self)
        ySubscriptYOffsetLabel = QLabel("ySubscriptYOffset:", self)
        ySuperscriptXSizeLabel = QLabel("ySuperscriptXSize:", self)
        ySuperscriptYSizeLabel = QLabel("ySuperscriptYSize:", self)
        ySuperscriptXOffsetLabel = QLabel("ySuperscriptXOffset:", self)
        ySuperscriptYOffsetLabel = QLabel("ySuperscriptYOffset:", self)
        yStrikeoutSizeLabel = QLabel("yStrikeoutSize:", self)
        yStrikeoutPositionLabel = QLabel("yStrikeoutPosition:", self)
        self.loadPositiveInteger(
            font, "openTypeOS2WeightClass", "usWeightClass")
        self.loadInteger(font, "openTypeOS2TypoAscender", "sTypoAscender")
        self.loadInteger(font, "openTypeOS2TypoDescender", "sTypoDescender")
        self.loadInteger(font, "openTypeOS2TypoLineGap", "sTypoLineGap")
        self.loadPositiveInteger(font, "openTypeOS2WinAscent", "usWinAscent")
        self.loadPositiveInteger(font, "openTypeOS2WinDescent", "usWinDescent")
        self.loadInteger(font, "openTypeOS2SubscriptXSize", "ySubscriptXSize")
        self.loadInteger(font, "openTypeOS2SubscriptYSize", "ySubscriptYSize")
        self.loadInteger(
            font, "openTypeOS2SubscriptXOffset", "ySubscriptXOffset")
        self.loadInteger(
            font, "openTypeOS2SubscriptYOffset", "ySubscriptYOffset")
        self.loadInteger(
            font, "openTypeOS2SuperscriptXSize", "ySuperscriptXSize")
        self.loadInteger(
            font, "openTypeOS2SuperscriptYSize", "ySuperscriptYSize")
        self.loadInteger(
            font, "openTypeOS2SuperscriptXOffset", "ySuperscriptXOffset")
        self.loadInteger(
            font, "openTypeOS2SuperscriptYOffset", "ySuperscriptYOffset")
        self.loadInteger(font, "openTypeOS2StrikeoutSize", "yStrikeoutSize")
        self.loadInteger(
            font, "openTypeOS2StrikeoutPosition", "yStrikeoutPosition")

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
        self.writePositiveInteger(
            font, "usWeightClass", "openTypeOS2WeightClass")
        self.writeInteger(font, "sTypoAscender", "openTypeOS2TypoAscender")
        self.writeInteger(font, "sTypoDescender", "openTypeOS2TypoDescender")
        self.writeInteger(font, "sTypoLineGap", "openTypeOS2TypoLineGap")
        self.writePositiveInteger(font, "usWinAscent", "openTypeOS2WinAscent")
        self.writePositiveInteger(
            font, "usWinDescent", "openTypeOS2WinDescent")
        self.writeInteger(font, "ySubscriptXSize", "openTypeOS2SubscriptXSize")
        self.writeInteger(font, "ySubscriptYSize", "openTypeOS2SubscriptYSize")
        self.writeInteger(
            font, "ySubscriptXOffset", "openTypeOS2SubscriptXOffset")
        self.writeInteger(
            font, "ySubscriptYOffset", "openTypeOS2SubscriptYOffset")
        self.writeInteger(
            font, "ySuperscriptXSize", "openTypeOS2SuperscriptXSize")
        self.writeInteger(
            font, "ySuperscriptYSize", "openTypeOS2SuperscriptYSize")
        self.writeInteger(
            font, "ySuperscriptXOffset", "openTypeOS2SuperscriptXOffset")
        self.writeInteger(
            font, "ySuperscriptYOffset", "openTypeOS2SuperscriptYOffset")
        self.writeInteger(font, "yStrikeoutSize", "openTypeOS2StrikeoutSize")
        self.writeInteger(
            font, "yStrikeoutPosition", "openTypeOS2StrikeoutPosition")

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

        # XXX: panose


class PostScriptTab(TabWidget):

    def __init__(self, font, parent=None):
        super().__init__(parent, name="PostScript")

        namingGroup = QGroupBox("Naming", self)
        # namingGroup.setFlat(True)
        namingLayout = QGridLayout(self)

        fontNameLabel = QLabel("FontName:", self)
        fullNameLabel = QLabel("FullName:", self)
        weightNameLabel = QLabel("WeightName:", self)
        uniqueIDLabel = QLabel("Unique ID:", self)
        self.loadString(font, "postscriptFontName", "fontName")
        self.loadString(font, "postscriptFullName", "fullName")
        self.loadString(font, "postscriptWeightName", "weightName")
        self.loadInteger(font, "postscriptUniqueID", "uniqueID")

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

        self.loadIntegerFloatList(font, "postscriptBlueValues", "blueValues")
        self.loadIntegerFloatList(font, "postscriptOtherBlues", "otherBlues")
        self.loadIntegerFloatList(font, "postscriptFamilyBlues", "familyBlues")
        self.loadIntegerFloatList(
            font, "postscriptFamilyOtherBlues", "familyOtherBlues")
        blueValuesLabel = QLabel("Blue values:", self)
        otherBluesLabel = QLabel("Other blues:", self)
        familyBluesLabel = QLabel("Family blues:", self)
        familyOtherBluesLabel = QLabel("Family other blues:", self)

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
        stemSnapHLabel = QLabel("StemSnapH:", self)
        blueScaleLabel = QLabel("Blue scale:", self)
        stemSnapVLabel = QLabel("StemSnapV:", self)
        blueShiftLabel = QLabel("Blue shift:", self)
        self.loadIntegerFloatList(font, "postscriptStemSnapH", "stemSnapH")
        self.loadIntegerFloatList(font, "postscriptStemSnapV", "stemSnapV")
        self.loadIntegerFloat(font, "postscriptBlueFuzz", "blueFuzz")
        self.loadIntegerFloat(font, "postscriptBlueScale", "blueScale")
        self.loadIntegerFloat(font, "postscriptBlueShift", "blueShift")

        forceBoldLabel = QLabel("Force bold:", self)
        self.loadBoolean(font, "postscriptForceBold", "forceBold")

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
        underlineThicknessLabel = QLabel("UnderlineThickness:", self)
        nominalWidthXLabel = QLabel("NominalWidthX:", self)
        underlinePositionLabel = QLabel("UnderlinePosition:", self)
        slantAngleLabel = QLabel("SlantAngle:", self)
        self.loadIntegerFloat(font, "postscriptDefaultWidthX", "defaultWidthX")
        self.loadIntegerFloat(font, "postscriptNominalWidthX", "nominalWidthX")
        self.loadIntegerFloat(
            font, "postscriptUnderlineThickness", "underlineThickness")
        self.loadIntegerFloat(
            font, "postscriptUnderlinePosition", "underlinePosition")
        self.loadIntegerFloat(font, "postscriptSlantAngle", "slantAngle")

        isFixedPitchLabel = QLabel("isFixedPitched:", self)
        self.loadBoolean(font, "postscriptIsFixedPitch", "isFixedPitch")

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
        self.loadString(font, "postscriptDefaultCharacter", "defaultCharacter")

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
        self.writeString(font, "fontName", "postscriptFontName")
        self.writeString(font, "fullName", "postscriptFullName")
        self.writeString(font, "weightName", "postscriptWeightName")
        self.writeInteger(font, "uniqueID", "postscriptUniqueID")
        self.writeIntegerFloatList(font, "blueValues", "postscriptBlueValues")
        self.writeIntegerFloatList(font, "otherBlues", "postscriptOtherBlues")
        self.writeIntegerFloatList(
            font, "familyBlues", "postscriptFamilyBlues")
        self.writeIntegerFloatList(
            font, "familyOtherBlues", "postscriptFamilyOtherBlues")
        self.writeIntegerFloatList(font, "stemSnapH", "postscriptStemSnapH")
        self.writeIntegerFloatList(font, "stemSnapV", "postscriptStemSnapV")
        self.writeIntegerFloat(font, "blueFuzz", "postscriptBlueFuzz")
        self.writeIntegerFloat(font, "blueScale", "postscriptBlueScale")
        self.writeIntegerFloat(font, "blueShift", "postscriptBlueShift")
        self.writeIntegerFloat(
            font, "defaultWidthX", "postscriptDefaultWidthX")
        self.writeIntegerFloat(
            font, "nominalWidthX", "postscriptNominalWidthX")
        self.writeIntegerFloat(
            font, "underlineThickness", "postscriptUnderlineThickness")
        self.writeIntegerFloat(
            font, "underlinePosition", "postscriptUnderlinePosition")
        self.writeIntegerFloat(font, "slantAngle", "postscriptSlantAngle")

        self.writeBoolean(font, "forceBold", "postscriptForceBold")
        self.writeBoolean(font, "isFixedPitch", "postscriptIsFixedPitch")

        self.writeString(
            font, "defaultCharacter", "postscriptDefaultCharacter")

        windowsCharacterSet = self.windowsCharacterSetDrop.currentIndex()
        if windowsCharacterSet == 0:
            font.info.postscriptWindowsCharacterSet = None
        else:
            font.info.postscriptWindowsCharacterSet = windowsCharacterSet
