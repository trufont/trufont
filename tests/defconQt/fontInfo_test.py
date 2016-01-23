import unittest
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QWidget
from defconQt.fontView import Application, MainWindow
from defconQt.fontInfo import InfoTabWidget
from defconQt.objects.defcon import TFont


class InfoTabWidgetTest(unittest.TestCase):

    app = Application(sys.argv)

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

    def setUp(self):
        self.infoTab = InfoTabWidget(None)

    def test_addNamedTab(self):
        tab1 = QWidget(None)
        tab1.name = "Test1"
        self.infoTab.addNamedTab(tab1)
        tab2 = self.infoTab.widget(0)
        self.assertEqual(tab1, tab2)
        self.assertEqual(tab1.name, tab2.name)

        tab2 = QWidget(None)
        tab2.name = "Test2"
        self.infoTab.addNamedTab(tab2)
        tab2 = self.infoTab.widget(0)
        self.assertEqual(tab1, tab2)
        self.assertEqual(tab1.name, tab2.name)


# TODO TabDialogTest

# TODO TabWidget

class TabTestCase(unittest.TestCase):

    app = Application(sys.argv)

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

    def setUp(self):
        font = TFont()
        font.info.unitsPerEm = 1000
        font.info.ascender = 750
        font.info.descender = -250
        font.info.capHeight = 750
        font.info.xHeight = 500

        self.mainWindow = MainWindow(font)
        self.mainWindow.fontInfo()
        self.font = self.mainWindow.font
        self.fontInfo = self.mainWindow.fontInfoWindow
        self.generalTab = self.fontInfo.tabWidget.widget(0)
        self.metricsTab = self.fontInfo.tabWidget.widget(1)
        self.openTypeTab = self.fontInfo.tabWidget.widget(2)
        self.OS2Tab = self.fontInfo.tabWidget.widget(3)
        self.postScriptTab = self.fontInfo.tabWidget.widget(4)
        self.fontInfo.show()

    def tearDown(self):
        self.fontInfo.close()

    def checkString(self, attr, attrName):
        attrEdit = getattr(self.tab, attr + "Edit")
        self.assertIsNone(getattr(self.font.info, attrName))
        self.assertEqual(attrEdit.text(), "")

        attrEdit.setText("Typeface " + attr)
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), "Typeface " + attr)

        attrEdit.setText("")
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

    def checkMultilineString(self, attr, attrName):
        attrEdit = getattr(self.tab, attr + "Edit")
        self.assertIsNone(getattr(self.font.info, attrName))
        self.assertEqual(attrEdit.toPlainText(), "")

        attrEdit.setPlainText("Typeface " + attr)
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), "Typeface " + attr)

        attrEdit.setPlainText("")
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

    def checkInteger(self, attr, attrName, value=0):
        attrEdit = getattr(self.tab, attr + "Edit")
        if value == 0:
            self.assertIsNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), "")
        else:
            self.assertIsNotNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), str(value))

        attrEdit.setText("123")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 123)

        attrEdit.setText("0")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 0)

        attrEdit.setText("-123")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), -123)

        attrEdit.setText("")
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

        validator = attrEdit.validator()
        self.assertIsInstance(validator, QIntValidator)
        self.assertEqual(validator.bottom(), QIntValidator().bottom())
        self.assertEqual(validator.top(), QIntValidator().top())

    def checkPositiveInteger(self, attr, attrName, value=0):
        attrEdit = getattr(self.tab, attr + "Edit")
        if value == 0:
            self.assertIsNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), "")
        else:
            self.assertIsNotNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), str(value))

        attrEdit.setText("123")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 123)

        attrEdit.setText("0")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 0)

        attrEdit.setText("")
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

        validator = attrEdit.validator()
        self.assertIsInstance(validator, QIntValidator)
        self.assertEqual(validator.bottom(), 0)
        self.assertEqual(validator.top(), QIntValidator().top())

    def checkNegativeInteger(self, attr, attrName, value=0):
        attrEdit = getattr(self.tab, attr + "Edit")
        if value == 0:
            self.assertIsNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), "")
        else:
            self.assertIsNotNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), str(value))

        attrEdit.setText("-123")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), -123)

        attrEdit.setText("0")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 0)

        attrEdit.setText("")
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

        validator = attrEdit.validator()
        self.assertIsInstance(validator, QIntValidator)
        self.assertEqual(validator.top(), 0)
        self.assertEqual(validator.bottom(), QIntValidator().bottom())

    def checkIntegerFloat(self, attr, attrName, value=0):
        attrEdit = getattr(self.tab, attr + "Edit")
        if value == 0:
            self.assertIsNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), "")
        else:
            self.assertIsNotNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), str(value))

        attrEdit.setText("123")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 123)

        attrEdit.setText("123.456")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 123.456)

        attrEdit.setText("0")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 0)

        attrEdit.setText("0.0")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 0.0)

        attrEdit.setText("-123")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), -123)

        attrEdit.setText("-123.456")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), -123.456)

        attrEdit.setText("")
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

        validator = attrEdit.validator()
        self.assertIsInstance(validator, QDoubleValidator)
        self.assertEqual(validator.bottom(), QDoubleValidator().bottom())
        self.assertEqual(validator.top(), QDoubleValidator().top())

    def checkPositiveIntegerFloat(self, attr, attrName, value=0):
        attrEdit = getattr(self.tab, attr + "Edit")
        if value == 0:
            self.assertIsNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), "")
        else:
            self.assertIsNotNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.text(), str(value))

        attrEdit.setText("123")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 123)

        attrEdit.setText("123.456")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 123.456)

        attrEdit.setText("0")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 0)

        attrEdit.setText("0.0")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 0.0)

        attrEdit.setText("")
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

        validator = attrEdit.validator()
        self.assertIsInstance(validator, QDoubleValidator)
        self.assertEqual(validator.bottom(), 0)
        self.assertEqual(validator.top(), QDoubleValidator().top())

    def checkIntegerFloatList(self, attr, attrName, maxLen=None, evenLen=None):
        attrEdit = getattr(self.tab, attr + "Edit")
        values = attrEdit.text()
        if values is "":
            self.assertEqual(getattr(self.font.info, attrName), [])
        else:
            attrEdit.setText("123 456 789 0")
            self.fontInfo.accept()
            self.assertIsNotNone(getattr(self.font.info, attrName))

        values = attrEdit.text().split(" ")
        for i, val in enumerate(values):
            if val != "":
                self.assertEqual(
                    int(val), getattr(self.font.info, attrName)[i])

        attrEdit.setText("123 456 789 0")
        self.fontInfo.accept()
        self.assertIsNotNone(getattr(self.font.info, attrName))

        # TODO: test validation

    def checkBoolean(self, attr, attrName):
        attrBox = getattr(self.tab, attr + "Box")
        self.assertTrue(attrBox.isTristate())

        value = attrBox.checkState()
        self.assertEqual(value, Qt.PartiallyChecked)
        self.assertEqual(getattr(self.font.info, attrName), None)

        attrBox.setCheckState(Qt.Checked)
        self.fontInfo.accept()
        value = attrBox.checkState()
        self.assertEqual(value, Qt.Checked)
        self.assertEqual(getattr(self.font.info, attrName), True)

        attrBox.setCheckState(Qt.Unchecked)
        self.fontInfo.accept()
        value = attrBox.checkState()
        self.assertEqual(value, Qt.Unchecked)
        self.assertEqual(getattr(self.font.info, attrName), False)


class GeneralTabTest(TabTestCase):

    def __init__(self, methodName):
        super().__init__(methodName)

    def setUp(self):
        super().setUp()
        self.tab = self.generalTab

    def test_GeneralTab_name(self):
        self.assertEqual(self.tab.name, "General")

    def test_familyName(self):
        self.checkString("familyName", "familyName")

    def test_styleName(self):
        self.checkString("styleName", "styleName")

    def test_copyright(self):
        self.checkMultilineString("copyright", "copyright")

    def test_trademark(self):
        self.checkString("trademark", "trademark")

    def test_designer(self):
        self.checkString("designer", "openTypeNameDesigner")

    def test_designerURL(self):
        self.checkString("designerURL", "openTypeNameDesignerURL")

    def test_manufacturer(self):
        self.checkString("manufacturer", "openTypeNameManufacturer")

    def test_manufacturerURL(self):
        self.checkString("manufacturerURL", "openTypeNameManufacturerURL")

    def test_license(self):
        self.checkMultilineString("license", "openTypeNameLicense")

    def test_licenseURL(self):
        self.checkString("licenseURL", "openTypeNameLicenseURL")

    def test_versionMajor(self):
        self.checkInteger("versionMajor", "versionMajor")

    def test_versionMinor(self):
        self.checkPositiveInteger("versionMinor", "versionMinor")


class MetricsTabTest(TabTestCase):

    def __init__(self, methodName):
        super().__init__(methodName)

    def setUp(self):
        super().setUp()
        self.tab = self.metricsTab

    def test_MetricsTab_name(self):
        self.assertEqual(self.tab.name, "Metrics")

    # TODO styleMapFamilyName

    def test_unitsPerEm(self):
        self.checkPositiveIntegerFloat(
            "unitsPerEm", "unitsPerEm", value="1000")

    def test_italicAngle(self):
        self.checkIntegerFloat("italicAngle", "italicAngle")

    def test_ascender(self):
        self.checkIntegerFloat("ascender", "ascender", 750)

    def test_descender(self):
        self.checkIntegerFloat("descender", "descender", -250)

    def test_capHeight(self):
        self.checkIntegerFloat("capHeight", "capHeight", 750)

    def test_xHeight(self):
        self.checkIntegerFloat("xHeight", "xHeight", 500)

    def test_noteEdit(self):
        self.checkMultilineString("note", "note")


class OpenTypeTabTest(TabTestCase):

    def __init__(self, methodName):
        super().__init__(methodName)

    def setUp(self):
        super().setUp()
        self.tab = self.openTypeTab

    def test_OpenTypeTab_name(self):
        self.assertEqual(self.tab.name, "OpenType")

    def test_preferredFamilyName(self):
        self.checkString(
            "preferredFamilyName", "openTypeNamePreferredFamilyName")

    def test_preferredSubfamilyName(self):
        self.checkString(
            "preferredSubfamilyName", "openTypeNamePreferredSubfamilyName")

    def test_compatibleFullName(self):
        self.checkString(
            "compatibleFullName", "openTypeNameCompatibleFullName")

    def test_WWSFamilyName(self):
        self.checkString("WWSFamilyName", "openTypeNameWWSFamilyName")

    def test_WWSSubfamilyName(self):
        self.checkString("WWSSubfamilyName", "openTypeNameWWSSubfamilyName")

    def test_version(self):
        self.checkString("version", "openTypeNameVersion")

    def test_uniqueID(self):
        self.checkString("uniqueID", "openTypeNameUniqueID")

    def test_description(self):
        self.checkString("description", "openTypeNameDescription")

    def test_sampleText(self):
        self.checkString("sampleText", "openTypeNameSampleText")

    def test_ascender(self):
        self.checkInteger("ascender", "openTypeHheaAscender")

    def test_descender(self):
        self.checkInteger("descender", "openTypeHheaDescender")

    def test_lineGap(self):
        self.checkInteger("lineGap", "openTypeHheaLineGap")

    def test_caretSlopeRise(self):
        self.checkInteger("caretSlopeRise", "openTypeHheaCaretSlopeRise")

    def test_caretSlopeRun(self):
        self.checkInteger("caretSlopeRun", "openTypeHheaCaretSlopeRun")

    def test_caretOffset(self):
        self.checkInteger("caretOffset", "openTypeHheaCaretOffset")

    def test_vertTypoAscender(self):
        self.checkInteger("vertTypoAscender", "openTypeVheaVertTypoAscender")

    def test_vertTypoDescender(self):
        self.checkInteger("vertTypoDescender", "openTypeVheaVertTypoDescender")

    def test_vertTypoLineGap(self):
        self.checkInteger("vertTypoLineGap", "openTypeVheaVertTypoLineGap")

    def test_vheaCaretSlopeRise(self):
        self.checkInteger("vheaCaretSlopeRise", "openTypeVheaCaretSlopeRise")

    def test_vheaCaretSlopeRun(self):
        self.checkInteger("vheaCaretSlopeRun", "openTypeVheaCaretSlopeRun")

    def test_vheaCaretOffset(self):
        self.checkInteger("vheaCaretOffset", "openTypeVheaCaretOffset")


class OS2TabTest(TabTestCase):

    def __init__(self, methodName):
        super().__init__(methodName)

    def setUp(self):
        super().setUp()
        self.tab = self.OS2Tab

    def test_OS2Tab_name(self):
        self.assertEqual(self.tab.name, "OS/2")

    # TODO: test_usWidthClassLabel()

    # TODO: test_fsSelection()

    # TODO: test_achVendorID()

    # TODO: fsType

    # XXX: ulUnicodeRange, ulCodePageRange are not implemented yet

    def test_usWeightClass(self):
        self.checkPositiveInteger("usWeightClass", "openTypeOS2WeightClass")

    def test_sTypoAscender(self):
        self.checkInteger("sTypoAscender", "openTypeOS2TypoAscender")

    def test_sTypoDescender(self):
        self.checkInteger("sTypoDescender", "openTypeOS2TypoDescender")

    def test_sTypoLineGap(self):
        self.checkInteger("sTypoLineGap", "openTypeOS2TypoLineGap")

    def test_usWinAscent(self):
        self.checkPositiveInteger("usWinAscent", "openTypeOS2WinAscent")

    def test_usWinDescent(self):
        self.checkPositiveInteger("usWinDescent", "openTypeOS2WinDescent")

    def test_ySubscriptXSize(self):
        self.checkInteger("ySubscriptXSize", "openTypeOS2SubscriptXSize")

    def test_ySubscriptYSize(self):
        self.checkInteger("ySubscriptYSize", "openTypeOS2SubscriptYSize")

    def test_ySubscriptXOffset(self):
        self.checkInteger("ySubscriptXOffset", "openTypeOS2SubscriptXOffset")

    def test_ySubscriptYOffset(self):
        self.checkInteger("ySubscriptYOffset", "openTypeOS2SubscriptYOffset")

    def test_ySuperscriptXSize(self):
        self.checkInteger("ySuperscriptXSize", "openTypeOS2SuperscriptXSize")

    def test_ySuperscriptYSize(self):
        self.checkInteger("ySuperscriptYSize", "openTypeOS2SuperscriptYSize")

    def test_ySuperscriptXOffset(self):
        self.checkInteger(
            "ySuperscriptXOffset", "openTypeOS2SuperscriptXOffset")

    def test_ySuperscriptYOffset(self):
        self.checkInteger(
            "ySuperscriptYOffset", "openTypeOS2SuperscriptYOffset")

    def test_yStrikeoutSize(self):
        self.checkInteger("yStrikeoutSize", "openTypeOS2StrikeoutSize")

    def test_yStrikeoutPosition(self):
        self.checkInteger("yStrikeoutPosition", "openTypeOS2StrikeoutPosition")

    # XXX: Panose is not implemented yet


class PostScriptTabTest(TabTestCase):

    def __init__(self, methodName):
        super().__init__(methodName)

    def setUp(self):
        super().setUp()
        self.tab = self.postScriptTab

    def test_PostScriptTab_name(self):
        self.assertEqual(self.tab.name, "PostScript")

    def test_fontName(self):
        self.checkString("fontName", "postscriptFontName")

    def test_fullName(self):
        self.checkString("fullName", "postscriptFullName")

    def test_weightName(self):
        self.checkString("weightName", "postscriptWeightName")

    def test_uniqueID(self):
        self.checkInteger("uniqueID", "postscriptUniqueID")

    def test_blueValues(self):
        self.checkIntegerFloatList("blueValues", "postscriptBlueValues")

    def test_otherBlues(self):
        self.checkIntegerFloatList("otherBlues", "postscriptOtherBlues")

    def test_familyBlues(self):
        self.checkIntegerFloatList("familyBlues", "postscriptFamilyBlues")

    def test_familyOtherBlues(self):
        self.checkIntegerFloatList(
            "familyOtherBlues", "postscriptFamilyOtherBlues")

    def test_stemSnapH(self):
        self.checkIntegerFloatList("stemSnapH", "postscriptStemSnapH")

    def test_stemSnapV(self):
        self.checkIntegerFloatList("stemSnapV", "postscriptStemSnapV")

    def test_blueFuzz(self):
        self.checkIntegerFloat("blueFuzz", "postscriptBlueFuzz")

    def test_blueScale(self):
        self.checkIntegerFloat("blueScale", "postscriptBlueScale")

    def test_forceBold(self):
        self.checkBoolean("forceBold", "postscriptForceBold")

    def test_blueShift(self):
        self.checkIntegerFloat("blueShift", "postscriptBlueShift")

    def test_defaultWidthX(self):
        self.checkIntegerFloat("defaultWidthX", "postscriptDefaultWidthX")

    def test_nominalWidthX(self):
        self.checkIntegerFloat("nominalWidthX", "postscriptNominalWidthX")

    def test_underlineThickness(self):
        self.checkIntegerFloat(
            "underlineThickness", "postscriptUnderlineThickness")

    def test_underlinePosition(self):
        self.checkIntegerFloat(
            "underlinePosition", "postscriptUnderlinePosition")

    def test_slantAngle(self):
        self.checkIntegerFloat("slantAngle", "postscriptSlantAngle")

    def test_isFixedPitch(self):
        self.checkBoolean("isFixedPitch", "postscriptIsFixedPitch")

    def test_defaultCharacter(self):
        self.checkString("defaultCharacter", "postscriptDefaultCharacter")

    # TODO: test_windowsCharacterSet


if __name__ == "__main__":
    unittest.main()
