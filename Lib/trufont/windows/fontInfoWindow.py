from PyQt5.QtCore import (
    QDate, QDateTime, QLocale, QRegularExpression, QTime, Qt)
from PyQt5.QtGui import (
    QRegularExpressionValidator, QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QGroupBox, QLabel, QLineEdit, QListView,
    QPlainTextEdit, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget,
    QScrollArea, QSpacerItem, QSizePolicy, QSpinBox)
from trufont.controls.nameTabWidget import NameTabWidget
from trufont.objects import settings


# TODO: add placeholder text (fallbacks) and update on font.info changed
# TODO: add gasp/name entries


def TransparentScrollArea(parent=None):
    scrollArea = QScrollArea(parent)
    scrollArea.setStyleSheet(".QScrollArea { background: transparent; }")
    scrollArea.viewport().setStyleSheet(
        ".QWidget { background: transparent; }")
    return scrollArea


class FontInfoWindow(QDialog):

    def __init__(self, font, parent=None):
        super().__init__(parent)
        self.font = font

        self.tabWidget = NameTabWidget(self)
        self.tabWidget.addNamedTab(GeneralTab(self.font))
        self.tabWidget.addNamedTab(LegalTab(self.font))
        self.tabWidget.addNamedTab(OpenTypeTab(self.font))
        self.tabWidget.addNamedTab(PostScriptTab(self.font))

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)

        self.setWindowTitle(self.tr("Font Info – {0} {1}").format(
            self.font.info.familyName, self.font.info.styleName))

        self.readSettings()

    def readSettings(self):
        geometry = settings.fontInfoWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)

    def writeSettings(self):
        settings.setFontInfoWindowGeometry(self.saveGeometry())

    def accept(self):
        for i in range(self.tabWidget.count()):
            self.tabWidget.widget(i).storeValues()
        super().accept()

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent


class TabWidget(QWidget):

    def __init__(self, font, parent=None, name=None):
        self.name = name
        self.font = font
        super().__init__(parent)

        self.loadFunc = {
            "s":   self.loadString,
            "s+":  self.loadMultilineString,
            "i":   self.loadInteger,
            "pi":  self.loadPositiveInteger,
            "if":  self.loadIntegerFloat,
            "pif": self.loadPositiveIntegerFloat,
            "if+": self.loadIntegerFloatList,
            "b":   self.loadBoolean}
        self.storeFunc = {
            "s":   self.storeString,
            "s+":  self.storeMultilineString,
            "i":   self.storeInteger,
            "pi":  self.storePositiveInteger,
            "if":  self.storeIntegerFloat,
            "pif": self.storePositiveIntegerFloat,
            "if+": self.storeIntegerFloatList,
            "b":   self.storeBoolean}
        self.attributeType = {}

    # Convenience method for loading simple optional attributes into a line
    # edit, spin box or boolean box.
    def loadCustomIntoForm(self, attribute, attrtype, labeltext, form):
        label = RCheckBox(labeltext)
        edit = self.load(attribute, attrtype)
        label.clicked.connect(edit.setEnabled)
        if getattr(self.font.info, attribute) is not None:
            label.setChecked(True)
        else:
            edit.setEnabled(False)
        form.addRow(label, edit)

        return edit

    def load(self, attribute, attrtype):
        if attrtype not in self.loadFunc:
            raise ValueError("`attrtype` must be listed in `self.loadFunc`.")

        self.attributeType[attribute] = attrtype
        edit = self.loadFunc[attrtype](attribute)

        return edit

    def store(self, attribute):
        if attribute not in self.attributeType:
            raise ValueError("You can only store attributes that were "
                             "previously `self.load()`ed.")

        attrtype = self.attributeType[attribute]
        self.storeFunc[attrtype](attribute)

    def loadString(self, attribute):
        value = getattr(self.font.info, attribute)
        edit = QLineEdit(value, self)
        setattr(self, attribute + "Edit", edit)
        return edit

    def storeString(self, attribute):
        edit = getattr(self, attribute + "Edit")
        value = None
        if edit.isEnabled():
            value = edit.text()
        setattr(self.font.info, attribute, value)

    def loadMultilineString(self, attribute):
        value = getattr(self.font.info, attribute)
        edit = QPlainTextEdit(value, self)
        setattr(self, attribute + "Edit", edit)
        return edit

    def storeMultilineString(self, attribute):
        edit = getattr(self, attribute + "Edit")
        value = None
        if edit.isEnabled():
            value = edit.toPlainText()
        setattr(self.font.info, attribute, value)

    def loadInteger(self, attribute):
        value = getattr(self.font.info, attribute)
        if value is None:
            value = 0
        edit = QSpinBox(self)
        edit.setRange(-2147483648, 2147483647)
        edit.setValue(value)
        setattr(self, attribute + "Edit", edit)
        return edit

    def storeInteger(self, attribute):
        edit = getattr(self, attribute + "Edit")
        value = edit.value()
        if edit.isEnabled():
            setattr(self.font.info, attribute, value)
        else:
            setattr(self.font.info, attribute, None)

    def loadPositiveInteger(self, attribute):
        value = getattr(self.font.info, attribute)
        if value is None:
            value = 0
        edit = QSpinBox(self)
        edit.setRange(0, 2147483647)
        edit.setValue(value)
        setattr(self, attribute + "Edit", edit)
        return edit

    storePositiveInteger = storeInteger

    def loadIntegerFloat(self, attribute):
        value = getattr(self.font.info, attribute)
        if value is None:
            value = 0
        edit = FloatSpinBox(self)
        edit.setRange(-2147483648, 2147483647)
        edit.setDecimals(8)
        edit.setValue(value)
        setattr(self, attribute + "Edit", edit)
        return edit

    def storeIntegerFloat(self, attribute):
        edit = getattr(self, attribute + "Edit")
        value = edit.value()
        if edit.isEnabled():
            if value - int(value) == 0:  # Store ints as actual ints
                setattr(self.font.info, attribute, int(value))
            else:
                setattr(self.font.info, attribute, float(value))
        else:
            setattr(self.font.info, attribute, None)

    def loadPositiveIntegerFloat(self, attribute):
        value = getattr(self.font.info, attribute)
        if value is None:
            value = 0
        edit = FloatSpinBox(self)
        edit.setRange(0, 2147483647)
        edit.setDecimals(8)
        edit.setValue(value)
        setattr(self, attribute + "Edit", edit)
        return edit

    storePositiveIntegerFloat = storeIntegerFloat

    def loadIntegerFloatList(self, attribute):
        values = " ".join(str(val)
                          for val in getattr(self.font.info, attribute))
        edit = QLineEdit(values, self)
        validator = QRegularExpressionValidator(self)
        validator.setRegularExpression(
            QRegularExpression("(-?\d+([,.]\d+)?\s*)*"))
        edit.setValidator(validator)
        setattr(self, attribute + "Edit", edit)
        return edit

    def storeIntegerFloatList(self, attribute):
        edit = getattr(self, attribute + "Edit")
        attributeValues = None
        if edit.isEnabled():
            values = edit.text().split()
            attributeValues = []
            for val in values:
                if "." in val:
                    attributeValues.append(float(val))
                elif "," in val:
                    v = val.replace(",", ".")
                    attributeValues.append(float(v))
                elif val not in ("", " "):
                    attributeValues.append(int(val))
        setattr(self.font.info, attribute, attributeValues)

    def loadBoolean(self, attribute):
        value = getattr(self.font.info, attribute)
        edit = QCheckBox(self)
        if value is None:
            edit.setChecked(False)
        else:
            edit.setChecked(value)
        setattr(self, attribute + "Edit", edit)
        return edit

    def storeBoolean(self, attribute):
        edit = getattr(self, attribute + "Edit")
        value = edit.isChecked()
        if edit.isEnabled():
            setattr(self.font.info, attribute, bool(value))
        else:
            setattr(self.font.info, attribute, None)


class GeneralTab(TabWidget):

    def __init__(self, font, parent=None):
        super().__init__(font, parent)
        self.name = self.tr("General")

        mainLayout = QVBoxLayout(self)

        # General metadata
        generalLayout = QHBoxLayout()

        # General general metadata
        g1FormLayout = QFormLayout()
        g1FormLayout.setLabelAlignment(Qt.AlignRight | Qt.AlignTrailing |
                                       Qt.AlignVCenter)

        familyNameLabel = QLabel(self.tr("Family name:"), self)
        edit = self.load("familyName", "s")
        g1FormLayout.addRow(familyNameLabel, edit)

        styleNameLabel = QLabel(self.tr("Style name:"), self)
        edit = self.load("styleName", "s")
        g1FormLayout.addRow(styleNameLabel, edit)

        styleMapLabel = RCheckBox(self.tr("Style map:"), self)
        styleMapLayout = QHBoxLayout()
        self.styleMapFamilyEdit = QLineEdit(font.info.styleMapFamilyName, self)
        self.styleMapStyleDrop = QComboBox(self)
        items = [self.tr("Regular"), self.tr("Italic"),
                 self.tr("Bold"), self.tr("Bold Italic")]
        self.styleMapStyleDrop.insertItems(0, items)
        styleMapLabel.clicked.connect(self.styleMapFamilyEdit.setEnabled)
        styleMapLabel.clicked.connect(self.styleMapStyleDrop.setEnabled)
        sn = font.info.styleMapStyleName
        styleNames = {"regular": 0, "italic": 1, "bold": 2, "bold italic": 3}
        if sn and sn in styleNames:  # XXX: need sanity checks?
            styleMapLabel.setChecked(True)
            self.styleMapStyleDrop.setCurrentIndex(styleNames[sn])
        else:
            self.styleMapFamilyEdit.setEnabled(False)
            self.styleMapStyleDrop.setEnabled(False)
        styleMapLayout.addWidget(self.styleMapFamilyEdit)
        styleMapLayout.addWidget(self.styleMapStyleDrop)
        g1FormLayout.addRow(styleMapLabel, styleMapLayout)

        versionLabel = QLabel(self.tr("Version:"), self)
        versionLayout = QHBoxLayout()
        editMajor = self.load("versionMajor", "i")
        versionLayout.addWidget(editMajor)
        versionLayout.setStretch(0, 1)
        versionDotLabel = QLabel(".", self)
        versionLayout.addWidget(versionDotLabel)
        editMinor = self.load("versionMinor", "pi")
        versionLayout.addWidget(editMinor)
        versionLayout.setStretch(2, 1)
        g1FormLayout.addRow(versionLabel, versionLayout)

        dateCreatedLabel = QLabel(self.tr("Date created:"), self)
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
        g1FormLayout.addRow(dateCreatedLabel, self.dateCreatedEdit)

        generalLayout.addLayout(g1FormLayout)
        generalLayout.setStretch(0, 1)

        # General metrics metadata
        g2FormLayout = QFormLayout()
        g2FormLayout.setLabelAlignment(Qt.AlignRight | Qt.AlignTrailing |
                                       Qt.AlignVCenter)

        unitsPerEmLabel = QLabel(self.tr("Units per em:"), self)
        edit = self.load("unitsPerEm", "pif")
        g2FormLayout.addRow(unitsPerEmLabel, edit)

        ascenderLabel = QLabel(self.tr("Ascender:"), self)
        edit = self.load("ascender", "if")
        g2FormLayout.addRow(ascenderLabel, edit)

        descenderLabel = QLabel(self.tr("Descender:"), self)
        edit = self.load("descender", "if")
        g2FormLayout.addRow(descenderLabel, edit)

        capHeightLabel = QLabel(self.tr("Cap height:"), self)
        edit = self.load("capHeight", "if")
        g2FormLayout.addRow(capHeightLabel, edit)

        xHeightLabel = QLabel(self.tr("x-height:"), self)
        edit = self.load("xHeight", "if")
        g2FormLayout.addRow(xHeightLabel, edit)

        italicAngleLabel = QLabel(self.tr("Italic angle:"), self)
        edit = self.load("italicAngle", "if")
        g2FormLayout.addRow(italicAngleLabel, edit)

        generalLayout.addLayout(g2FormLayout)

        mainLayout.addLayout(generalLayout)

        # Notes
        notesLayout = QFormLayout()
        notesLayout.setLabelAlignment(Qt.AlignRight | Qt.AlignTrailing |
                                      Qt.AlignVCenter)
        notesLayout.setRowWrapPolicy(QFormLayout.WrapAllRows)

        noteLabel = QLabel(self.tr("Notes:"), self)
        edit = self.load("note", "s+")
        noteSizePolicy = edit.sizePolicy()
        noteSizePolicy.setVerticalStretch(1)
        edit.setSizePolicy(noteSizePolicy)
        notesLayout.addRow(noteLabel, edit)

        mainLayout.addLayout(notesLayout)

    def storeValues(self):
        self.store("familyName")
        self.store("styleName")

        font = self.font
        if (self.styleMapFamilyEdit.isEnabled() and
                self.styleMapStyleDrop.isEnabled()):
            font.info.styleMapFamilyName = self.styleMapFamilyEdit.text()
            styleNames = ["regular", "italic", "bold", "bold italic"]
            sn = styleNames[self.styleMapStyleDrop.currentIndex()]
            font.info.styleMapStyleName = sn
        else:
            font.info.styleMapFamilyName = None
            font.info.styleMapStyleName = None

        self.store("versionMajor")
        self.store("versionMinor")

        font.info.openTypeHeadCreated = QLocale.c().toString(
                self.dateCreatedEdit.dateTime(),
                "yyyy/MM/dd hh:mm:ss")

        self.store("unitsPerEm")
        self.store("italicAngle")
        self.store("ascender")
        self.store("descender")
        self.store("capHeight")
        self.store("xHeight")

        self.store("note")


class LegalTab(TabWidget):

    def __init__(self, font, parent=None):
        super().__init__(font, parent)
        self.name = self.tr("Legal")

        mainLayout = QFormLayout(self)
        mainLayout.setLabelAlignment(Qt.AlignRight | Qt.AlignTrailing |
                                     Qt.AlignVCenter)

        designerLabel = QLabel(self.tr("Designer:"), self)
        edit = self.load("openTypeNameDesigner", "s")
        mainLayout.addRow(designerLabel, edit)

        designerURLLabel = QLabel(self.tr("Designer URL:"), self)
        edit = self.load("openTypeNameDesignerURL", "s")
        mainLayout.addRow(designerURLLabel, edit)

        manufacturerLabel = QLabel(self.tr("Manufacturer:"), self)
        edit = self.load("openTypeNameManufacturer", "s")
        mainLayout.addRow(manufacturerLabel, edit)

        manufacturerURLLabel = QLabel(self.tr("Manufacturer URL:"), self)
        edit = self.load("openTypeNameManufacturerURL", "s")
        mainLayout.addRow(manufacturerURLLabel, edit)

        copyrightLabel = QLabel(self.tr("Copyright:"), self)
        edit = self.load("copyright", "s+")
        copyrightSizePolicy = edit.sizePolicy()
        copyrightSizePolicy.setVerticalStretch(1)
        edit.setSizePolicy(copyrightSizePolicy)
        mainLayout.addRow(copyrightLabel, edit)

        licenseLabel = QLabel(self.tr("License:"), self)
        edit = self.load("openTypeNameLicense", "s+")
        licenseSizePolicy = edit.sizePolicy()
        licenseSizePolicy.setVerticalStretch(1)
        edit.setSizePolicy(licenseSizePolicy)
        mainLayout.addRow(licenseLabel, edit)

        licenseURLLabel = QLabel(self.tr("License URL:"), self)
        edit = self.load("openTypeNameLicenseURL", "s")
        mainLayout.addRow(licenseURLLabel, edit)

        trademarkLabel = QLabel(self.tr("Trademark:"), self)
        edit = self.load("trademark", "s")
        mainLayout.addRow(trademarkLabel, edit)

    def storeValues(self):
        self.store("openTypeNameDesigner")
        self.store("openTypeNameDesignerURL")
        self.store("openTypeNameManufacturer")
        self.store("openTypeNameManufacturerURL")
        self.store("copyright")
        self.store("openTypeNameLicense")
        self.store("openTypeNameLicenseURL")
        self.store("trademark")


class OpenTypeTab(TabWidget):

    def __init__(self, font, parent=None):
        super().__init__(font, parent)
        self.name = self.tr("OpenType")

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        tableScrollArea = TransparentScrollArea(self)
        tableScrollArea.setWidgetResizable(True)
        tableArea = QWidget(tableScrollArea)
        tableScrollArea.setWidget(tableArea)
        mainLayout.addWidget(tableScrollArea)

        tableLayout = QVBoxLayout(tableArea)

        tableLayout.addWidget(self.setupHeadGroup())
        tableLayout.addWidget(self.setupNameGroup())
        tableLayout.addWidget(self.setupHheaGroup())
        tableLayout.addWidget(self.setupVheaGroup())
        tableLayout.addWidget(self.setupOs2Group())

        spacer = QSpacerItem(
            10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        tableLayout.addItem(spacer)

    def setupHeadGroup(self):
        headGroup = QGroupBox(self.tr("head table"))
        headLayout = QVBoxLayout(headGroup)

        headAttributesLayout = QFormLayout()
        headAttributesLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.loadCustomIntoForm("openTypeHeadLowestRecPPEM", "pi",
                                self.tr("Lowest rec. PPEM:"),
                                headAttributesLayout)

        flagsLabel = RCheckBox(self.tr("Flags:"))
        self.flagsEdit = BitListView(self)
        flagsLabel.clicked.connect(self.flagsEdit.setEnabled)
        flagItems = [
            self.tr("Bit 0: Baseline for font at y=0."),
            self.tr("Bit 1: Left sidebearing point at x=0."),
            self.tr("Bit 2: Instructions may depend on point size."),
            self.tr("Bit 3: Force ppem to integer values for all "
                    "internal scaler math."),
            self.tr("Bit 4: Instructions may alter advance width."),
            self.tr("Bit 11: Font data is 'lossless'."),
            self.tr("Bit 12: Font converted."),
            self.tr("Bit 13: Font optimized for ClearType™."),
            self.tr("Bit 14: Last Resort font.")]
        itemToFlagMap = {0: 0, 1: 1, 2: 2, 3: 3,
                         4: 4, 5: 11, 6: 12, 7: 13, 8: 14}
        flags = self.font.info.openTypeHeadFlags
        model = QStandardItemModel(9, 1)
        for index, elem in enumerate(flagItems):
            item = QStandardItem()
            item.setText(elem)
            item.setCheckable(True)
            bit = itemToFlagMap[index]
            if flags is not None and bit in flags:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            model.setItem(index, item)
        self.flagsEdit.setModel(model)
        if flags is not None:
            flagsLabel.setChecked(True)
        else:
            self.flagsEdit.setEnabled(False)
        headAttributesLayout.addRow(flagsLabel, self.flagsEdit)

        headLayout.addLayout(headAttributesLayout)

        return headGroup

    def setupNameGroup(self):
        nameGroup = QGroupBox(self.tr("name table"))
        nameLayout = QVBoxLayout(nameGroup)

        nameAttributesLayout = QFormLayout()
        nameAttributesLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.loadCustomIntoForm("openTypeNamePreferredFamilyName", "s",
                                self.tr("Pref. family name:"),
                                nameAttributesLayout)
        self.loadCustomIntoForm("openTypeNamePreferredSubfamilyName", "s",
                                self.tr("Pref. subfamily name:"),
                                nameAttributesLayout)
        self.loadCustomIntoForm("openTypeNameCompatibleFullName", "s",
                                self.tr("Compatible full name:"),
                                nameAttributesLayout)
        self.loadCustomIntoForm("openTypeNameWWSFamilyName", "s",
                                self.tr("WWS family name:"),
                                nameAttributesLayout)
        self.loadCustomIntoForm("openTypeNameWWSSubfamilyName", "s",
                                self.tr("WWS subfamily name:"),
                                nameAttributesLayout)
        self.loadCustomIntoForm("openTypeNameVersion", "s",
                                self.tr("Version:"),
                                nameAttributesLayout)
        self.loadCustomIntoForm("openTypeNameUniqueID", "s",
                                self.tr("Unique ID:"),
                                nameAttributesLayout)
        self.loadCustomIntoForm("openTypeNameDescription", "s",
                                self.tr("Description:"),
                                nameAttributesLayout)
        self.loadCustomIntoForm("openTypeNameSampleText", "s",
                                self.tr("Sample text:"),
                                nameAttributesLayout)

        nameLayout.addLayout(nameAttributesLayout)

        return nameGroup

    def setupHheaGroup(self):
        hheaGroup = QGroupBox(self.tr("hhea table"))
        hheaLayout = QVBoxLayout(hheaGroup)

        hheaAttributesLayout = QFormLayout()
        hheaAttributesLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.loadCustomIntoForm("openTypeHheaAscender", "i",
                                self.tr("Ascender:"),
                                hheaAttributesLayout)
        self.loadCustomIntoForm("openTypeHheaDescender", "i",
                                self.tr("Descender:"),
                                hheaAttributesLayout)
        self.loadCustomIntoForm("openTypeHheaLineGap", "i",
                                self.tr("LineGap:"),
                                hheaAttributesLayout)
        self.loadCustomIntoForm("openTypeHheaCaretSlopeRise", "i",
                                self.tr("caretSlopeRise:"),
                                hheaAttributesLayout)
        self.loadCustomIntoForm("openTypeHheaCaretSlopeRun", "i",
                                self.tr("caretSlopeRun:"),
                                hheaAttributesLayout)
        self.loadCustomIntoForm("openTypeHheaCaretOffset", "i",
                                self.tr("caretOffset:"),
                                hheaAttributesLayout)

        hheaLayout.addLayout(hheaAttributesLayout)

        return hheaGroup

    def setupVheaGroup(self):
        vheaGroup = QGroupBox(self.tr("vhea table"))
        vheaLayout = QVBoxLayout(vheaGroup)

        vheaAttributesLayout = QFormLayout()
        vheaAttributesLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.loadCustomIntoForm("openTypeVheaVertTypoAscender", "i",
                                self.tr("V. Ascender:"),
                                vheaAttributesLayout)
        self.loadCustomIntoForm("openTypeVheaVertTypoDescender", "i",
                                self.tr("V. Descender:"),
                                vheaAttributesLayout)
        self.loadCustomIntoForm("openTypeVheaVertTypoLineGap", "i",
                                self.tr("V. LineGap:"),
                                vheaAttributesLayout)
        self.loadCustomIntoForm("openTypeVheaCaretSlopeRise", "i",
                                self.tr("V. caretSlopeRise:"),
                                vheaAttributesLayout)
        self.loadCustomIntoForm("openTypeVheaCaretSlopeRun", "i",
                                self.tr("V. caretSlopeRun:"),
                                vheaAttributesLayout)
        self.loadCustomIntoForm("openTypeVheaCaretOffset", "i",
                                self.tr("V. caretOffset:"),
                                vheaAttributesLayout)

        vheaLayout.addLayout(vheaAttributesLayout)

        return vheaGroup

    def setupOs2Group(self):
        font = self.font
        os2Group = QGroupBox(self.tr("os2 table"))
        os2Layout = QVBoxLayout(os2Group)

        os2AttributesLayout = QFormLayout()
        os2AttributesLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.loadCustomIntoForm("openTypeOS2VendorID", "s",
                                self.tr("Vendor ID:"),
                                os2AttributesLayout).setMaxLength(4)

        usWidthClassLabel = RCheckBox(self.tr("Width class:"))
        self.usWidthClassDrop = QComboBox(self)
        items = [
            self.tr("Ultra-condensed"), self.tr("Extra-condensed"),
            self.tr("Condensed"), self.tr("Semi-Condensed"),
            self.tr("Medium (normal)"), self.tr("Semi-expanded"),
            self.tr("Expanded"), self.tr("Extra-expanded"),
            self.tr("Ultra-expanded")]
        self.usWidthClassDrop.insertItems(0, items)
        usWidthClassLabel.clicked.connect(self.usWidthClassDrop.setEnabled)
        if font.info.openTypeOS2WidthClass:
            usWidthClassLabel.setChecked(True)
            self.usWidthClassDrop.setCurrentIndex(
                font.info.openTypeOS2WidthClass - 1)
        else:
            self.usWidthClassDrop.setEnabled(False)
            self.usWidthClassDrop.setCurrentIndex(4)
        os2AttributesLayout.addRow(usWidthClassLabel, self.usWidthClassDrop)

        usWeightClassLabel = RCheckBox(self.tr("Weight class:"))
        self.usWeightClassDrop = QComboBox(self)
        items = [
            self.tr("Thin"), self.tr("Extra-light (Ultra-light)"),
            self.tr("Light"), self.tr("Normal (Regular)"),
            self.tr("Medium"), self.tr("Semi-bold (Demi-bold)"),
            self.tr("Bold"), self.tr("Extra-bold (Ultra-bold)"),
            self.tr("Black (Heavy)")]
        self.usWeightClassDrop.insertItems(0, items)
        usWeightClassLabel.clicked.connect(self.usWeightClassDrop.setEnabled)
        wc = font.info.openTypeOS2WeightClass
        if wc and wc % 100 == 0:
            usWeightClassLabel.setChecked(True)
            self.usWeightClassDrop.setCurrentIndex(
                font.info.openTypeOS2WeightClass / 100 - 1)
        else:
            self.usWeightClassDrop.setEnabled(False)
            self.usWeightClassDrop.setCurrentIndex(3)
        os2AttributesLayout.addRow(usWeightClassLabel, self.usWeightClassDrop)

        fsSelectionLabel = RCheckBox(self.tr("fsSelection:"))
        fsSelection = font.info.openTypeOS2Selection
        self.fsSelectionList = BitListView(self)
        self.fsSelectionList.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        fsSelectionLabel.clicked.connect(self.fsSelectionList.setEnabled)
        items = [
            self.tr("Bit 1 UNDERSCORE"), self.tr("Bit 2 NEGATIVE"),
            self.tr("Bit 3 OUTLINED"), self.tr("Bit 4 STRIKEOUT"),
            self.tr("Bit 7 USE_TYPO_METRICS"), self.tr("Bit 8 WWS"),
            self.tr("Bit 9 OBLIQUE")]
        itemToFlagMap = {0: 1, 1: 2, 2: 3, 3: 4, 4: 7, 5: 8, 6: 9}
        # http://stackoverflow.com/a/26613163
        model = QStandardItemModel(7, 1)
        for index, elem in enumerate(items):
            item = QStandardItem()
            item.setText(elem)
            item.setCheckable(True)
            bit = itemToFlagMap[index]
            if fsSelection is not None and bit in fsSelection:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            model.setItem(index, item)
        self.fsSelectionList.setModel(model)
        if fsSelection is not None:
            fsSelectionLabel.setChecked(True)
        else:
            self.fsSelectionList.setEnabled(False)
        os2AttributesLayout.addRow(fsSelectionLabel, self.fsSelectionList)

        # XXX: disabled QCheckBoxes eat scroll events?! Can't scroll past
        # disabled checkboxes unless outside their rectangle.
        fsTypeLabel = RCheckBox(self.tr("Embedding:"))
        fsType = font.info.openTypeOS2Type
        self.fsTypeDrop = QComboBox(self)
        items = [
            self.tr("No embedding restrictions"),
            self.tr("Restricted embedding"),
            self.tr("Preview and print embedding allowed"),
            self.tr("Editable embedding allowed")]
        self.noSubsettingBox = QCheckBox(self.tr("No subsetting"))
        self.bitmapEmbeddingOnlyBox = QCheckBox(
            self.tr("Bitmap embedding only"))
        fsTypeLabel.clicked.connect(self.fsTypeDrop.setEnabled)
        fsTypeLabel.clicked.connect(self.noSubsettingBox.setEnabled)
        fsTypeLabel.clicked.connect(self.bitmapEmbeddingOnlyBox.setEnabled)
        fsTypeLabel.clicked.connect(
            lambda: self._updateFsTypeVisibility(
                self.fsTypeDrop.currentIndex()))
        self.fsTypeDrop.currentIndexChanged[int].connect(
            self._updateFsTypeVisibility)
        self.fsTypeDrop.insertItems(0, items)
        if fsType is not None:
            fsTypeLabel.setChecked(True)
            for i in range(1, 4):
                if i in fsType:
                    self.fsTypeDrop.setCurrentIndex(i)
                    break
            self.noSubsettingBox.setChecked(8 in fsType)
            self.bitmapEmbeddingOnlyBox.setChecked(9 in fsType)
        else:
            self.fsTypeDrop.setEnabled(False)
        embeddingLayout = QVBoxLayout()
        embeddingLayout.addWidget(self.fsTypeDrop)
        embeddingLayout.addWidget(self.noSubsettingBox)
        embeddingLayout.addWidget(self.bitmapEmbeddingOnlyBox)
        os2AttributesLayout.addRow(fsTypeLabel, embeddingLayout)

        panoseLabel = RCheckBox(self.tr("PANOSE:"))
        panose = font.info.openTypeOS2Panose
        panoseLayout = QFormLayout()
        panoseLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        panoseFamilyLabel = QLabel(self.tr("Family:"))
        panoseFamilyTypes = [
            self.tr("Any"), self.tr("No fit"), self.tr("Text and display"),
            self.tr("Script"), self.tr("Decorative"), self.tr("Pictorial")]
        self.panoseFamilyDrop = QComboBox(self)
        self.panoseFamilyDrop.insertItems(0, panoseFamilyTypes)
        panoseLayout.addRow(panoseFamilyLabel, self.panoseFamilyDrop)
        panoseSerifsLabel = QLabel(self.tr("Serifs:"))
        panoseSerifsTypes = [
            self.tr("Any"), self.tr("No fit"), self.tr("Cove"),
            self.tr("Obtuse cove"), self.tr("Square cove"),
            self.tr("Obtuse square cove"),
            self.tr("Square"), self.tr("Thin"), self.tr("Bone"),
            self.tr("Exaggerated"), self.tr("Triangle"),
            self.tr("Normal sans-serif"), self.tr("Obtuse sans-serif"),
            self.tr("Perp sans-serif"), self.tr("Flared"), self.tr("Rounded")]
        self.panoseSerifsDrop = QComboBox(self)
        self.panoseSerifsDrop.insertItems(0, panoseSerifsTypes)
        panoseLayout.addRow(panoseSerifsLabel, self.panoseSerifsDrop)
        panoseWeightLabel = QLabel(self.tr("Weight:"))
        panoseWeightTypes = [
            self.tr("Any"), self.tr("No fit"),
            self.tr("Very light"), self.tr("Light"), self.tr("Thin"),
            self.tr("Book"), self.tr("Medium"), self.tr("Demibold"),
            self.tr("Bold"), self.tr("Heavy"), self.tr("Black"),
            self.tr("Nord")]
        self.panoseWeightDrop = QComboBox(self)
        self.panoseWeightDrop.insertItems(0, panoseWeightTypes)
        panoseLayout.addRow(panoseWeightLabel, self.panoseWeightDrop)
        panoseProportionLabel = QLabel(self.tr("Proportion:"))
        panoseProportionTypes = [
            self.tr("Any"), self.tr("No fit"),
            self.tr("Old style"), self.tr("Modern"), self.tr("Even width"),
            self.tr("Expanded"), self.tr("Condensed"),
            self.tr("Very expanded"), self.tr("Very condensed"),
            self.tr("Monospaced")]
        self.panoseProportionDrop = QComboBox(self)
        self.panoseProportionDrop.insertItems(0, panoseProportionTypes)
        panoseLayout.addRow(panoseProportionLabel, self.panoseProportionDrop)
        panoseContrastLabel = QLabel(self.tr("Contrast:"))
        panoseContrastTypes = [
            self.tr("Any"), self.tr("No fit"),
            self.tr("None"), self.tr("Very low"), self.tr("Low"),
            self.tr("Medium low"), self.tr("Medium"), self.tr("Medium high"),
            self.tr("High"), self.tr("Very high")]
        self.panoseContrastDrop = QComboBox(self)
        self.panoseContrastDrop.insertItems(0, panoseContrastTypes)
        panoseLayout.addRow(panoseContrastLabel, self.panoseContrastDrop)
        panoseStrokeVariationLabel = QLabel(self.tr("Stroke variation:"))
        panoseStrokeVariationTypes = [
            self.tr("Any"), self.tr("No fit"),
            self.tr("Gradual/diagonal"), self.tr("Gradual/transitional"),
            self.tr("Gradual/vertical"), self.tr("Gradual/horizontal"),
            self.tr("Rapid/vertical"), self.tr("Rapid/horizontal"),
            self.tr("Instant/vertical")]
        self.panoseStrokeVariationDrop = QComboBox(self)
        self.panoseStrokeVariationDrop.insertItems(
            0, panoseStrokeVariationTypes)
        panoseLayout.addRow(panoseStrokeVariationLabel,
                            self.panoseStrokeVariationDrop)
        panoseArmStyleLabel = QLabel(self.tr("Arm style:"))
        panoseArmStyleTypes = [
            self.tr("Any"), self.tr("No fit"),
            self.tr("Straight arms/horizontal"),
            self.tr("Straight arms/wedge"),
            self.tr("Straight arms/vertical"),
            self.tr("Straight arms/single-serif"),
            self.tr("Straight arms/double-serif"),
            self.tr("Nonstraight arms/horizontal"),
            self.tr("Nonstraight arms/wedge"),
            self.tr("Nonstraight arms/vertical"),
            self.tr("Nonstraight arms/single-serif"),
            self.tr("Nonstraight arms/double-serif")]
        self.panoseArmStyleDrop = QComboBox(self)
        self.panoseArmStyleDrop.insertItems(0, panoseArmStyleTypes)
        panoseLayout.addRow(panoseArmStyleLabel, self.panoseArmStyleDrop)
        panoseLetterformLabel = QLabel(self.tr("Letterform:"))
        panoseLetterformTypes = [
            self.tr("Any"), self.tr("No fit"),
            self.tr("Normal/contact"), self.tr("Normal/weighted"),
            self.tr("Normal/boxed"), self.tr("Normal/flattened"),
            self.tr("Normal/rounded"), self.tr("Normal/off center"),
            self.tr("Normal/square"), self.tr("Oblique/contact"),
            self.tr("Oblique/weighted"), self.tr("Oblique/boxed"),
            self.tr("Oblique/flattened"), self.tr("Oblique/rounded"),
            self.tr("Oblique/off center"), self.tr("Oblique/square")]
        self.panoseLetterformDrop = QComboBox(self)
        self.panoseLetterformDrop.insertItems(0, panoseLetterformTypes)
        panoseLayout.addRow(panoseLetterformLabel, self.panoseLetterformDrop)
        panoseMidlineLabel = QLabel(self.tr("Midline:"))
        panoseMidlineTypes = [
            self.tr("Any"), self.tr("No fit"),
            self.tr("Standard/trimmed"), self.tr("Standard/pointed"),
            self.tr("Standard/serifed"), self.tr("High/trimmed"),
            self.tr("High/pointed"), self.tr("High/serifed"),
            self.tr("Constant/trimmed"), self.tr("Constant/pointed"),
            self.tr("Constant/serifed"), self.tr("Low/trimmed"),
            self.tr("Low/pointed"), self.tr("Low/serifed")]
        self.panoseMidlineDrop = QComboBox(self)
        self.panoseMidlineDrop.insertItems(0, panoseMidlineTypes)
        panoseLayout.addRow(panoseMidlineLabel, self.panoseMidlineDrop)
        panoseXHeightLabel = QLabel(self.tr("x-Height:"))
        panoseXHeightTypes = [
            self.tr("Any"), self.tr("No fit"),
            self.tr("Constant/small"), self.tr("Constant/standard"),
            self.tr("Constant/large"), self.tr("Ducking/small"),
            self.tr("Ducking/standard"), self.tr("Ducking/large")]
        self.panoseXHeightDrop = QComboBox(self)
        self.panoseXHeightDrop.insertItems(0, panoseXHeightTypes)
        panoseLayout.addRow(panoseXHeightLabel, self.panoseXHeightDrop)
        panoseLabel.clicked.connect(self.panoseFamilyDrop.setEnabled)
        panoseLabel.clicked.connect(self.panoseSerifsDrop.setEnabled)
        panoseLabel.clicked.connect(self.panoseWeightDrop.setEnabled)
        panoseLabel.clicked.connect(self.panoseProportionDrop.setEnabled)
        panoseLabel.clicked.connect(self.panoseContrastDrop.setEnabled)
        panoseLabel.clicked.connect(self.panoseStrokeVariationDrop.setEnabled)
        panoseLabel.clicked.connect(self.panoseArmStyleDrop.setEnabled)
        panoseLabel.clicked.connect(self.panoseLetterformDrop.setEnabled)
        panoseLabel.clicked.connect(self.panoseMidlineDrop.setEnabled)
        panoseLabel.clicked.connect(self.panoseXHeightDrop.setEnabled)
        if panose:
            panoseLabel.setChecked(True)
            self.panoseFamilyDrop.setCurrentIndex(panose[0])
            self.panoseSerifsDrop.setCurrentIndex(panose[1])
            self.panoseWeightDrop.setCurrentIndex(panose[2])
            self.panoseProportionDrop.setCurrentIndex(panose[3])
            self.panoseContrastDrop.setCurrentIndex(panose[4])
            self.panoseStrokeVariationDrop.setCurrentIndex(panose[5])
            self.panoseArmStyleDrop.setCurrentIndex(panose[6])
            self.panoseLetterformDrop.setCurrentIndex(panose[7])
            self.panoseMidlineDrop.setCurrentIndex(panose[8])
            self.panoseXHeightDrop.setCurrentIndex(panose[9])
        else:
            self.panoseFamilyDrop.setEnabled(False)
            self.panoseSerifsDrop.setEnabled(False)
            self.panoseWeightDrop.setEnabled(False)
            self.panoseProportionDrop.setEnabled(False)
            self.panoseContrastDrop.setEnabled(False)
            self.panoseStrokeVariationDrop.setEnabled(False)
            self.panoseArmStyleDrop.setEnabled(False)
            self.panoseLetterformDrop.setEnabled(False)
            self.panoseMidlineDrop.setEnabled(False)
            self.panoseXHeightDrop.setEnabled(False)
        os2AttributesLayout.addRow(panoseLabel, panoseLayout)

        unicodeRangesLabel = RCheckBox(self.tr("Unicode ranges:"))
        unicodeRangesItems = [
            self.tr("Basic Latin (0000–007F)"),
            self.tr("Latin-1 Supplement (0080–00FF)"),
            self.tr("Latin Extended-A (0100–017F)"),
            self.tr("Latin Extended-B (0180–024F)"),
            self.tr("IPA Extensions (0250–02AF, 1D00–1D7F, 1D80–1DBF)"),
            self.tr("Spacing Modifier Letters, Modifier Tone Letters "
                    "(02B0–02FF, A700–A71F)"),
            self.tr("Combining Diacritical Marks (0300–036F, 1DC0–1DFF)"),
            self.tr("Greek and Coptic (0370–03FF)"),
            self.tr("Coptic (2C80–2CFF)"),
            self.tr("Cyrillic and extensions (0400–04FF, 0500–052F, "
                    "2DE0–2DFF, A640–A69F)"),
            self.tr("Armenian (0530–058F)"),
            self.tr("Hebrew (0590–05FF)"),
            self.tr("Vai (A500–A63F)"),
            self.tr("Arabic (0600–06FF, 0750–077F)"),
            self.tr("NKo (07C0–07FF)"),
            self.tr("Devanagari (0900–097F)"),
            self.tr("Bengali (0980–09FF)"),
            self.tr("Gurmukhi (0A00–0A7F)"),
            self.tr("Gujarati (0A80–0AFF)"),
            self.tr("Oriya (0B00–0B7F)"),
            self.tr("Tamil (0B80–0BFF)"),
            self.tr("Telugu (0C00–0C7F)"),
            self.tr("Kannada (0C80–0CFF)"),
            self.tr("Malayalam (0D00–0D7F)"),
            self.tr("Thai (0E00–0E7F)"),
            self.tr("Lao (0E80–0EFF)"),
            self.tr("Georgian (10A0–10FF, 2D00–2D2F)"),
            self.tr("Balinese (1B00–1B7F)"),
            self.tr("Hangul Jamo (1100–11FF)"),
            self.tr("Latin Extended Additional (1E00–1EFF, 2C60–2C7F, "
                    "A720–A7FF)"),
            self.tr("Greek Extended (1F00–1FFF)"),
            self.tr("Punctuation (2000–206F, 2E00–2E7F)"),
            self.tr("Superscripts And Subscripts (2070–209F)"),
            self.tr("Currency Symbols (20A0–20CF)"),
            self.tr("Combining Diacritical Marks For Symbols "
                    "(20D0–20FF)"),
            self.tr("Letterlike Symbols (2100–214F)"),
            self.tr("Number Forms (2150–218F)"),
            self.tr("Arrows (2190–21FF, 27F0–27FF, 2900–297F, "
                    "2B00–2BFF)"),
            self.tr("Mathematical Operators (2200–22FF, 2A00–2AFF, "
                    "27C0–27EF, 2980–29FF)"),
            self.tr("Miscellaneous Technical (2300–23FF)"),
            self.tr("Control Pictures (2400–243F)"),
            self.tr("Optical Character Recognition (2440–245F)"),
            self.tr("Enclosed Alphanumerics (2460–24FF)"),
            self.tr("Box Drawing (2500–257F)"),
            self.tr("Block Elements (2580–259F)"),
            self.tr("Geometric Shapes (25A0–25FF)"),
            self.tr("Miscellaneous Symbols (2600–26FF)"),
            self.tr("Dingbats (2700–27BF)"),
            self.tr("CJK Symbols And Punctuation (3000–303F)"),
            self.tr("Hiragana (3040–309F)"),
            self.tr("Katakana (30A0–30FF, 31F0–31FF)"),
            self.tr("Bopomofo (3100–312F, 31A0–31BF)"),
            self.tr("Hangul Compatibility Jamo (3130–318F)"),
            self.tr("Phags-pa (A840–A87F)"),
            self.tr("Enclosed CJK Letters And Months (3200–32FF)"),
            self.tr("CJK Compatibility (3300–33FF)"),
            self.tr("Hangul Syllables (AC00–D7AF)"),
            self.tr("Non-Plane 0 * (D800–DFFF)"),
            self.tr("Phoenician (10900–1091F)"),
            self.tr("CJK Unified Ideographs (2E80–2EFF, 2F00–2FDF, "
                    "2FF0–2FFF, 3190–319F, 3400–4DBF, 4E00–9FFF, "
                    "20000–2A6DF)"),
            self.tr("Private Use Area (plane 0) (E000–F8FF)"),
            self.tr("CJK Strokes (31C0–31EF, F900–FAFF, 2F800–2FA1F)"),
            self.tr("Alphabetic Presentation Forms (FB00–FB4F)"),
            self.tr("Arabic Presentation Forms-A (FB50–FDFF)"),
            self.tr("Combining Half Marks (FE20–FE2F)"),
            self.tr("CJK Vertical Forms (FE10–FE1F, FE30–FE4F)"),
            self.tr("Small Form Variants (FE50–FE6F)"),
            self.tr("Arabic Presentation Forms-B (FE70–FEFF)"),
            self.tr("Halfwidth And Fullwidth Forms (FF00–FFEF)"),
            self.tr("Specials (FFF0–FFFF)"),
            self.tr("Tibetan (0F00–0FFF)"),
            self.tr("Syriac (0700–074F)"),
            self.tr("Thaana (0780–07BF)"),
            self.tr("Sinhala (0D80–0DFF)"),
            self.tr("Myanmar (1000–109F)"),
            self.tr("Ethiopic (1200–137F, 1380–139F, 2D80–2DDF)"),
            self.tr("Cherokee (13A0–13FF)"),
            self.tr("Unified Canadian Aboriginal Syllabics (1400–167F)"),
            self.tr("Ogham (1680–169F)"),
            self.tr("Runic (16A0–16FF)"),
            self.tr("Khmer (1780–17FF, 19E0–19FF)"),
            self.tr("Mongolian (1800–18AF)"),
            self.tr("Braille Patterns (2800–28FF)"),
            self.tr("Yi Syllables (A000–A48F, A490–A4CF)"),
            self.tr("Tagalog, Hanunoo, Buhid, Tagbanwa (1700–171F, "
                    "1720–173F, 1740–175F, 1760–177F)"),
            self.tr("Old Italic (10300–1032F)"),
            self.tr("Gothic (10330–1034F)"),
            self.tr("Deseret (10400–1044F)"),
            self.tr("Greek and Byzantine Musical Symbols (1D000–1D0FF, "
                    "1D100–1D1FF, 1D200–1D24F)"),
            self.tr("Mathematical Alphanumeric Symbols (1D400–1D7FF)"),
            self.tr("Private Use (planes 15 and 16) "
                    "(FF000–FFFFD, 100000–10FFFD)"),
            self.tr("Variation Selectors (FE00–FE0F, E0100–E01EF)"),
            self.tr("Tags (E0000–E007F)"),
            self.tr("Limbu (1900–194F)"),
            self.tr("Tai Le (1950–197F)"),
            self.tr("New Tai Lue (1980–19DF)"),
            self.tr("Buginese (1A00–1A1F)"),
            self.tr("Glagolitic (2C00–2C5F)"),
            self.tr("Tifinagh (2D30–2D7F)"),
            self.tr("Yijing Hexagram Symbols (4DC0–4DFF)"),
            self.tr("Syloti Nagri (A800–A82F)"),
            self.tr("Linear B, Aegean Numbers (10000–1007F, "
                    "10080–100FF, 10100–1013F)"),
            self.tr("Ancient Greek Numbers (10140–1018F)"),
            self.tr("Ugaritic (10380–1039F)"),
            self.tr("Old Persian (103A0–103DF)"),
            self.tr("Shavian (10450–1047F)"),
            self.tr("Osmanya (10480–104AF)"),
            self.tr("Cypriot Syllabary (10800–1083F)"),
            self.tr("Kharoshthi (10A00–10A5F)"),
            self.tr("Tai Xuan Jing Symbols (1D300–1D35F)"),
            self.tr("Cuneiform (12000–123FF, 12400–1247F)"),
            self.tr("Counting Rod Numerals (1D360–1D37F)"),
            self.tr("Sundanese (1B80–1BBF)"),
            self.tr("Lepcha (1C00–1C4F)"),
            self.tr("Ol Chiki (1C50–1C7F)"),
            self.tr("Saurashtra (A880–A8DF)"),
            self.tr("Kayah Li (A900–A92F)"),
            self.tr("Rejang (A930–A95F)"),
            self.tr("Cham (AA00–AA5F)"),
            self.tr("Ancient Symbols (10190–101CF)"),
            self.tr("Phaistos Disc (101D0–101FF)"),
            self.tr("Carian, Lycian, Lydian (102A0–102DF, 10280–1029F, "
                    "10920–1093F)"),
            self.tr("Domino tiles, Mahjong tiles (1F030–1F09F, "
                    "1F000–1F02F)")]
        unicodeRanges = font.info.openTypeOS2UnicodeRanges
        self.unicodeRangesEdit = QListView(self)  # too long for BitListView
        self.unicodeRangesEdit.setMinimumHeight(200)
        self.unicodeRangesEdit.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        uRModel = QStandardItemModel(len(unicodeRangesItems), 1)
        for index, elem in enumerate(unicodeRangesItems):
            item = QStandardItem()
            item.setText(elem)
            item.setCheckable(True)
            bit = index
            if unicodeRanges is not None and bit in unicodeRanges:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            uRModel.setItem(index, item)
        self.unicodeRangesEdit.setModel(uRModel)
        unicodeRangesLabel.clicked.connect(self.unicodeRangesEdit.setEnabled)
        if unicodeRanges is not None:
            unicodeRangesLabel.setChecked(True)
        else:
            self.unicodeRangesEdit.setEnabled(False)
        os2AttributesLayout.addRow(unicodeRangesLabel, self.unicodeRangesEdit)

        codePageRangesLabel = RCheckBox(self.tr("Code page ranges:"))
        codePageRangesItems = [
            self.tr("Latin 1 (1252)"),
            self.tr("Latin 2: Eastern Europe (1250)"),
            self.tr("Cyrillic (1251)"),
            self.tr("Greek (1253)"),
            self.tr("Turkish (1254)"),
            self.tr("Hebrew (1255)"),
            self.tr("Arabic (1256)"),
            self.tr("Windows Baltic (1257)"),
            self.tr("Vietnamese (1258)"),
            self.tr("Thai (874)"),
            self.tr("JIS/Japan (932)"),
            self.tr("Chinese: Simplified chars, PRC and Singapore (936)"),
            self.tr("Korean Wansung (949)"),
            self.tr("Chinese: Traditional chars, Taiwan and Hong Kong (950)"),
            self.tr("Korean Johab (1361)"),
            self.tr("Macintosh Character Set (US Roman)"),
            self.tr("OEM Character Set"),
            self.tr("Symbol Character Set"),
            self.tr("IBM Greek (869)"),
            self.tr("MS-DOS Russian (866)"),
            self.tr("MS-DOS Nordic (865)"),
            self.tr("Arabic (864)"),
            self.tr("MS-DOS Canadian French (863)"),
            self.tr("Hebrew (862)"),
            self.tr("MS-DOS Icelandic (861)"),
            self.tr("MS-DOS Portuguese (860)"),
            self.tr("IBM Turkish (857)"),
            self.tr("IBM Cyrillic; primarily Russian (855)"),
            self.tr("Latin 2 (852)"),
            self.tr("MS-DOS Baltic (775)"),
            self.tr("Greek; former 437 G (737)"),
            self.tr("Arabic; ASMO 708 (708)"),
            self.tr("WE/Latin 1 (850)"),
            self.tr("US (437)")]
        codePageRanges = font.info.openTypeOS2CodePageRanges
        self.codePageRangesEdit = QListView(self)  # too long for BitListView
        self.codePageRangesEdit.setMinimumHeight(200)
        self.codePageRangesEdit.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        cPRModel = QStandardItemModel(len(codePageRangesItems), 1)
        for index, elem in enumerate(codePageRangesItems):
            item = QStandardItem()
            item.setText(elem)
            item.setCheckable(True)
            bit = index
            if index > 17:
                bit += 30
            elif index > 14:
                bit += 14
            elif index > 8:
                bit += 6
            if codePageRanges is not None and bit in codePageRanges:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            cPRModel.setItem(index, item)
        self.codePageRangesEdit.setModel(cPRModel)
        codePageRangesLabel.clicked.connect(self.codePageRangesEdit.setEnabled)
        if codePageRanges is not None:
            codePageRangesLabel.setChecked(True)
        else:
            self.codePageRangesEdit.setEnabled(False)
        os2AttributesLayout.addRow(
            codePageRangesLabel, self.codePageRangesEdit)

        self.loadCustomIntoForm("openTypeOS2TypoAscender", "i",
                                self.tr("TypoAscender:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2TypoDescender", "i",
                                self.tr("TypoDescender:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2TypoLineGap", "i",
                                self.tr("TypoLineGap:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2WinAscent", "pi",
                                self.tr("usWinAscent:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2WinDescent", "pi",
                                self.tr("usWinDescent:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2SubscriptXSize", "i",
                                self.tr("ySubscriptXSize:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2SubscriptYSize", "i",
                                self.tr("ySubscriptYSize:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2SubscriptXOffset", "i",
                                self.tr("ySubscriptXOffset:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2SubscriptYOffset", "i",
                                self.tr("ySubscriptYOffset:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2SuperscriptXSize", "i",
                                self.tr("ySuperscriptXSize:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2SuperscriptYSize", "i",
                                self.tr("ySuperscriptYSize:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2SuperscriptXOffset", "i",
                                self.tr("ySuperscriptXOffset:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2SuperscriptYOffset", "i",
                                self.tr("ySuperscriptYOffset:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2StrikeoutSize", "i",
                                self.tr("yStrikeoutSize:"),
                                os2AttributesLayout)
        self.loadCustomIntoForm("openTypeOS2StrikeoutPosition", "i",
                                self.tr("yStrikeoutPosition:"),
                                os2AttributesLayout)

        os2Layout.addLayout(os2AttributesLayout)

        return os2Group

    def _updateFsTypeVisibility(self, index):
        if index == 0 or not self.fsTypeDrop.isEnabled():
            self.noSubsettingBox.setEnabled(False)
            self.bitmapEmbeddingOnlyBox.setEnabled(False)
        else:
            self.noSubsettingBox.setEnabled(True)
            self.bitmapEmbeddingOnlyBox.setEnabled(True)

    def storeValues(self):
        font = self.font

        # head table
        self.store("openTypeHeadLowestRecPPEM")
        if self.flagsEdit.isEnabled():
            headFlags = []
            itemToFlagMap = {0: 0, 1: 1, 2: 2, 3: 3,
                             4: 4, 5: 11, 6: 12, 7: 13, 8: 14}
            model = self.flagsEdit.model()
            for index in range(model.rowCount()):
                item = model.item(index)
                if item.checkState() == Qt.Checked:
                    headFlags.append(itemToFlagMap[index])
            font.info.openTypeHeadFlags = headFlags
        else:
            font.info.openTypeHeadFlags = None

        # name table
        self.store("openTypeNamePreferredFamilyName")
        self.store("openTypeNamePreferredSubfamilyName")
        self.store("openTypeNameCompatibleFullName")
        self.store("openTypeNameWWSFamilyName")
        self.store("openTypeNameWWSSubfamilyName")
        # XXX: Implement name records
        self.store("openTypeNameVersion")
        self.store("openTypeNameUniqueID")
        self.store("openTypeNameDescription")
        self.store("openTypeNameSampleText")

        # hhea table
        self.store("openTypeHheaAscender")
        self.store("openTypeHheaDescender")
        self.store("openTypeHheaLineGap")
        self.store("openTypeHheaCaretSlopeRise")
        self.store("openTypeHheaCaretSlopeRun")
        self.store("openTypeHheaCaretOffset")

        # vhea table
        self.store("openTypeVheaVertTypoAscender")
        self.store("openTypeVheaVertTypoDescender")
        self.store("openTypeVheaVertTypoLineGap")
        self.store("openTypeVheaCaretSlopeRise")
        self.store("openTypeVheaCaretSlopeRun")
        self.store("openTypeVheaCaretOffset")

        # XXX: Implement GASP table

        # TODO: see if data needs to be padded to 4 chars.
        # I think that this is to be deferred to ufo2fdk(?)
        self.store("openTypeOS2VendorID")

        if self.fsSelectionList.isEnabled():
            itemToFlagMap = {0: 1, 1: 2, 2: 3, 3: 4, 4: 7, 5: 8, 6: 9}
            fsSelectionModel = self.fsSelectionList.model()
            fsSelection = []
            for i in range(7):
                item = fsSelectionModel.item(i)
                if item.checkState() == Qt.Checked:
                    fsSelection.append(itemToFlagMap[i])
            font.info.openTypeOS2Selection = fsSelection
        else:
            font.info.openTypeOS2Selection = None

        if self.fsTypeDrop.isEnabled():
            fsTypeIndex = self.fsTypeDrop.currentIndex()
            fsType = []
            if fsTypeIndex > 0:
                fsType.append(fsTypeIndex)
                if self.noSubsettingBox.isChecked():
                    fsType.append(8)
                if self.bitmapEmbeddingOnlyBox.isChecked():
                    fsType.append(9)
            font.info.openTypeOS2Type = fsType
        else:
            font.info.openTypeOS2Type = None

        if self.usWidthClassDrop.isEnabled():
            font.info.openTypeOS2WidthClass = (
                self.usWidthClassDrop.currentIndex() + 1)
        else:
            font.info.openTypeOS2WidthClass = None

        if self.usWeightClassDrop.isEnabled():
            font.info.openTypeOS2WeightClass = (
                (self.usWeightClassDrop.currentIndex() + 1) * 100)
        else:
            font.info.openTypeOS2WeightClass = None

        if self.panoseFamilyDrop.isEnabled():
            panose = [
                self.panoseFamilyDrop.currentIndex(),
                self.panoseSerifsDrop.currentIndex(),
                self.panoseWeightDrop.currentIndex(),
                self.panoseProportionDrop.currentIndex(),
                self.panoseContrastDrop.currentIndex(),
                self.panoseStrokeVariationDrop.currentIndex(),
                self.panoseArmStyleDrop.currentIndex(),
                self.panoseLetterformDrop.currentIndex(),
                self.panoseMidlineDrop.currentIndex(),
                self.panoseXHeightDrop.currentIndex()]
            font.info.openTypeOS2Panose = panose
        else:
            font.info.openTypeOS2Panose = None

        if self.unicodeRangesEdit.isEnabled():
            unicodeRanges = []
            model = self.unicodeRangesEdit.model()
            for index in range(model.rowCount()):
                item = model.item(index)
                if item.checkState() == Qt.Checked:
                    unicodeRanges.append(index)
            font.info.openTypeOS2UnicodeRanges = unicodeRanges
        else:
            font.info.openTypeOS2UnicodeRanges = None

        if self.codePageRangesEdit.isEnabled():
            codePageRanges = []
            model = self.codePageRangesEdit.model()
            for index in range(model.rowCount()):
                item = model.item(index)
                if item.checkState() == Qt.Checked:
                    bit = index
                    if index > 17:
                        bit += 30
                    elif index > 14:
                        bit += 14
                    elif index > 8:
                        bit += 6
                    codePageRanges.append(bit)
            font.info.openTypeOS2CodePageRanges = codePageRanges
        else:
            font.info.openTypeOS2CodePageRanges = None

        self.store("openTypeOS2TypoAscender")
        self.store("openTypeOS2TypoDescender")
        self.store("openTypeOS2TypoLineGap")
        self.store("openTypeOS2WinAscent")
        self.store("openTypeOS2WinDescent")
        self.store("openTypeOS2SubscriptXSize")
        self.store("openTypeOS2SubscriptYSize")
        self.store("openTypeOS2SubscriptXOffset")
        self.store("openTypeOS2SubscriptYOffset")
        self.store("openTypeOS2SuperscriptXSize")
        self.store("openTypeOS2SuperscriptYSize")
        self.store("openTypeOS2SuperscriptXOffset")
        self.store("openTypeOS2SuperscriptYOffset")
        self.store("openTypeOS2StrikeoutSize")
        self.store("openTypeOS2StrikeoutPosition")


class PostScriptTab(TabWidget):

    def __init__(self, font, parent=None):
        super().__init__(font, parent)
        self.name = self.tr("PostScript")

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        tableScrollArea = TransparentScrollArea(self)
        tableScrollArea.setWidgetResizable(True)
        tableArea = QWidget(tableScrollArea)
        tableScrollArea.setWidget(tableArea)
        mainLayout.addWidget(tableScrollArea)

        tableLayout = QVBoxLayout(tableArea)

        # Naming
        namingGroup = QGroupBox(self.tr("Naming"))
        namingLayout = QFormLayout(namingGroup)
        namingLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.loadCustomIntoForm("postscriptFontName", "s",
                                self.tr("FontName:"),
                                namingLayout)
        self.loadCustomIntoForm("postscriptFullName", "s",
                                self.tr("FullName:"),
                                namingLayout)
        self.loadCustomIntoForm("postscriptWeightName", "s",
                                self.tr("WeightName:"),
                                namingLayout)
        self.loadCustomIntoForm("postscriptUniqueID", "i",
                                self.tr("UniqueID:"),
                                namingLayout)

        tableLayout.addWidget(namingGroup)

        # Hints
        hintsGroup = QGroupBox(self.tr("Hints"))
        hintsLayout = QFormLayout(hintsGroup)
        hintsLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.loadCustomIntoForm("postscriptBlueValues", "if+",
                                self.tr("BlueValues:"),
                                hintsLayout)
        self.loadCustomIntoForm("postscriptOtherBlues", "if+",
                                self.tr("OtherBlues:"),
                                hintsLayout)
        self.loadCustomIntoForm("postscriptFamilyBlues", "if+",
                                self.tr("FamilyBlues:"),
                                hintsLayout)
        self.loadCustomIntoForm("postscriptFamilyOtherBlues", "if+",
                                self.tr("FamilyOtherBlues:"),
                                hintsLayout)

        self.loadCustomIntoForm("postscriptBlueFuzz", "if",
                                self.tr("BlueFuzz:"),
                                hintsLayout)
        self.loadCustomIntoForm("postscriptBlueScale", "if",
                                self.tr("BlueScale:"),
                                hintsLayout)
        self.loadCustomIntoForm("postscriptBlueShift", "if",
                                self.tr("BlueShift:"),
                                hintsLayout)

        self.loadCustomIntoForm("postscriptStemSnapH", "if+",
                                self.tr("StemSnapH:"),
                                hintsLayout)
        self.loadCustomIntoForm("postscriptStemSnapV", "if+",
                                self.tr("StemSnapV:"),
                                hintsLayout)

        self.loadCustomIntoForm("postscriptForceBold", "b",
                                self.tr("ForceBold:"),
                                hintsLayout)

        tableLayout.addWidget(hintsGroup)

        # Metrics
        metricsGroup = QGroupBox(self.tr("Metrics"))
        metricsLayout = QFormLayout(metricsGroup)
        metricsLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.loadCustomIntoForm("postscriptDefaultWidthX", "if",
                                self.tr("DefaultWidthX:"),
                                metricsLayout)
        self.loadCustomIntoForm("postscriptNominalWidthX", "if",
                                self.tr("NominalWidthX:"),
                                metricsLayout)
        self.loadCustomIntoForm("postscriptUnderlineThickness", "if",
                                self.tr("UnderlineThickness:"),
                                metricsLayout)
        self.loadCustomIntoForm("postscriptUnderlinePosition", "if",
                                self.tr("UnderlinePosition:"),
                                metricsLayout)
        self.loadCustomIntoForm("postscriptSlantAngle", "if",
                                self.tr("SlantAngle:"),
                                metricsLayout)
        self.loadCustomIntoForm("postscriptIsFixedPitch", "b",
                                self.tr("isFixedPitch:"),
                                metricsLayout)

        tableLayout.addWidget(metricsGroup)

        # Characters
        charactersGroup = QGroupBox(self.tr("Characters"))
        charactersLayout = QFormLayout(charactersGroup)
        charactersLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.loadCustomIntoForm("postscriptDefaultCharacter", "s",
                                self.tr("Default character:"),
                                charactersLayout)

        windowsCharacterSetLabel = RCheckBox(self.tr("Windows character set:"))
        self.windowsCharacterSetDrop = QComboBox(self)
        windowsCharacterSetLabel.clicked.connect(
            self.windowsCharacterSetDrop.setEnabled)
        items = [
            self.tr("ANSI"), self.tr("Default"),
            self.tr("Symbol"), self.tr("Macintosh"), self.tr("Shift JIS"),
            self.tr("Hangul"), self.tr("Hangul (Johab)"), self.tr("GB2312"),
            self.tr("Chinese BIG5"), self.tr("Greek"), self.tr("Turkish"),
            self.tr("Vietnamese"), self.tr("Hebrew"), self.tr("Arabic"),
            self.tr("Baltic"), self.tr("Bitstream"), self.tr("Cyrillic"),
            self.tr("Thai"), self.tr("Eastern European"), self.tr("OEM")]
        self.windowsCharacterSetDrop.insertItems(0, items)
        if font.info.postscriptWindowsCharacterSet is not None:
            windowsCharacterSetLabel.setChecked(True)
            self.windowsCharacterSetDrop.setCurrentIndex(
                font.info.postscriptWindowsCharacterSet)
        else:
            self.windowsCharacterSetDrop.setEnabled(False)
        charactersLayout.addRow(windowsCharacterSetLabel,
                                self.windowsCharacterSetDrop)

        tableLayout.addWidget(charactersGroup)

        spacer = QSpacerItem(
            10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        tableLayout.addItem(spacer)

    def storeValues(self):
        self.store("postscriptFontName")
        self.store("postscriptFullName")
        self.store("postscriptWeightName")
        self.store("postscriptUniqueID")

        self.store("postscriptBlueValues")
        self.store("postscriptOtherBlues")
        self.store("postscriptFamilyBlues")
        self.store("postscriptFamilyOtherBlues")
        self.store("postscriptBlueFuzz")
        self.store("postscriptBlueScale")
        self.store("postscriptBlueShift")
        self.store("postscriptStemSnapH")
        self.store("postscriptStemSnapV")

        self.store("postscriptDefaultWidthX")
        self.store("postscriptNominalWidthX")
        self.store("postscriptUnderlineThickness")
        self.store("postscriptUnderlinePosition")
        self.store("postscriptSlantAngle")
        self.store("postscriptForceBold")
        self.store("postscriptIsFixedPitch")

        self.store("postscriptDefaultCharacter")
        font = self.font
        windowsCharacterSet = self.windowsCharacterSetDrop
        if windowsCharacterSet.isEnabled():
            font.info.postscriptWindowsCharacterSet = (
                windowsCharacterSet.currentIndex())
        else:
            font.info.postscriptWindowsCharacterSet = None

# ------------------
# Supporting widgets
# ------------------


class BitListView(QListView):
    """
    A QListView to display bit fields. Resizes automatically to fit all flags
    without vertical scroll bars, no horizontal scroll bars.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    # https://forum.qt.io/topic/40717/set-size-of-the-qlistview-to-fit-to-it-s-content/7  # noqa
    def sizeHint(self):
        hint = super().sizeHint()

        model = self.model()
        if model:
            extraHeight = self.height() - self.viewport().height()
            vRect = self.visualRect(
                model.index(model.rowCount() - 1, self.modelColumn()))
            hint.setHeight(vRect.y() + vRect.height() + extraHeight)

        return hint


class FloatSpinBox(QDoubleSpinBox):
    """
    Hides decimals unless used but shows decimal point to hint at the type of
    box. No more "250,00000000", just "250,".
    """

    def textFromValue(self, value):
        decimalPoint = QLocale().decimalPoint()
        if value.is_integer():
            return "{0}{1}".format(str(int(value)), decimalPoint)
        else:
            return str(value).replace(".", decimalPoint)


class RCheckBox(QCheckBox):
    """
    A QCheckBox with reversed check box for better alignment of custom
    parameter layouts.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayoutDirection(Qt.RightToLeft)
