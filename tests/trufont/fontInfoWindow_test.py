from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from trufont.controls.nameTabWidget import NameTabWidget
from trufont.objects.application import Application
from trufont.objects.defcon import TFont
from trufont.windows.fontWindow import FontWindow
import sys
import unittest


class NameTabWidgetTest(unittest.TestCase):

    app = Application(sys.argv)

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

    def setUp(self):
        self.infoTab = NameTabWidget(None)

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
        self.font = TFont.new()

        self.mainWindow = FontWindow(self.font)
        self.mainWindow.fontInfo()
        self.fontInfo = self.mainWindow._infoWindow
        self.generalTab = self.fontInfo.tabWidget.widget(0)
        self.legalTab = self.fontInfo.tabWidget.widget(1)
        self.openTypeTab = self.fontInfo.tabWidget.widget(2)
        self.postScriptTab = self.fontInfo.tabWidget.widget(3)
        self.fontInfo.show()

    def tearDown(self):
        self.fontInfo.close()

    def checkString(self, attrName):
        attrEdit = getattr(self.tab, attrName + "Edit")
        attrEdit.setEnabled(True)

        self.assertIsNone(getattr(self.font.info, attrName))
        self.assertEqual(attrEdit.text(), "")

        attrEdit.setText("Typeface " + attrName)
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName),
                         "Typeface " + attrName)

        attrEdit.setEnabled(False)
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

    def checkMultilineString(self, attrName):
        attrEdit = getattr(self.tab, attrName + "Edit")
        attrEdit.setEnabled(True)

        self.assertIsNone(getattr(self.font.info, attrName))
        self.assertEqual(attrEdit.toPlainText(), "")

        attrEdit.setPlainText("Typeface \n" + attrName)
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName),
                         "Typeface \n" + attrName)

        attrEdit.setEnabled(False)
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

    def checkInteger(self, attrName, value=0):
        attrEdit = getattr(self.tab, attrName + "Edit")
        attrEdit.setEnabled(True)

        if value == 0:
            self.assertIsNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.value(), 0)
        else:
            self.assertIsNotNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.value(), value)

        attrEdit.setValue(123)
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 123)

        attrEdit.setValue(0)
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 0)

        attrEdit.setValue(-123)
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), -123)

        attrEdit.setEnabled(False)
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

        self.assertEqual(attrEdit.minimum(), -2147483648)
        self.assertEqual(attrEdit.maximum(), 2147483647)

    def checkPositiveInteger(self, attrName, value=0):
        attrEdit = getattr(self.tab, attrName + "Edit")
        attrEdit.setEnabled(True)

        if value == 0:
            self.assertIsNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.value(), 0)
        else:
            self.assertIsNotNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.value(), value)

        attrEdit.setValue(123)
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 123)

        attrEdit.setValue(0)
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), 0)

        attrEdit.setEnabled(False)
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

        self.assertEqual(attrEdit.minimum(), 0)
        self.assertEqual(attrEdit.maximum(), 2147483647)

    def checkIntegerFloat(self, attrName, value=0):
        attrEdit = getattr(self.tab, attrName + "Edit")
        attrEdit.setEnabled(True)

        if value == 0:
            self.assertIsNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.value(), 0)
        else:
            self.assertIsNotNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.value(), value)

        attrEdit.setValue(123)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, 123)

        attrEdit.setValue(123.000)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, 123)

        attrEdit.setValue(123.456)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, float))
        self.assertEqual(attr, 123.456)

        attrEdit.setValue(0)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, 0)

        attrEdit.setValue(0.0)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, 0)

        attrEdit.setValue(-123)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, -123)

        attrEdit.setValue(-123.000)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, -123)

        attrEdit.setValue(-123.456)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, float))
        self.assertEqual(attr, -123.456)

        attrEdit.setEnabled(False)
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

        self.assertEqual(attrEdit.minimum(), -2147483648)
        self.assertEqual(attrEdit.maximum(), 2147483647)

    def checkPositiveIntegerFloat(self, attrName, value=0):
        attrEdit = getattr(self.tab, attrName + "Edit")
        attrEdit.setEnabled(True)

        if value == 0:
            self.assertIsNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.value(), 0)
        else:
            self.assertIsNotNone(getattr(self.font.info, attrName))
            self.assertEqual(attrEdit.value(), value)

        attrEdit.setValue(123)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, 123)

        attrEdit.setValue(123.000)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, 123)

        attrEdit.setValue(123.456)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, float))
        self.assertEqual(attr, 123.456)

        attrEdit.setValue(0)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, 0)

        attrEdit.setValue(0.0)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertTrue(isinstance(attr, int))
        self.assertEqual(attr, 0)

        attrEdit.setEnabled(False)
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))

        self.assertEqual(attrEdit.minimum(), 0)
        self.assertEqual(attrEdit.maximum(), 2147483647)

    # XXX: Implement maxLen, evenLen?
    def checkIntegerFloatList(self, attrName, maxLen=None, evenLen=None):
        attrEdit = getattr(self.tab, attrName + "Edit")
        attrEdit.setEnabled(True)

        attrEdit.setText("")
        self.fontInfo.accept()
        self.assertEqual(getattr(self.font.info, attrName), [])

        attrEdit.setText("123 456 789 0")
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertEqual(attr, [123, 456, 789, 0])

        attrEdit.setText("123,0 456,1 789.11111112 789,11111113 790 791")
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        self.assertEqual(attr,
                         [123, 456.1, 789.11111112, 789.11111113, 790, 791])

        attrEdit.setEnabled(False)
        self.fontInfo.accept()
        attr = getattr(self.font.info, attrName)
        # These are apparently always [], never None.
        if attrName in ["postscriptBlueValues", "postscriptOtherBlues",
                        "postscriptFamilyBlues",
                        "postscriptFamilyOtherBlues",
                        "postscriptStemSnapH", "postscriptStemSnapV"]:
            self.assertEqual(attr, [])
        else:
            self.assertIsNone(attr)

    def checkBoolean(self, attrName):
        attrEdit = getattr(self.tab, attrName + "Edit")
        attrEdit.setEnabled(True)

        # Most checkboxes are governed by a parent checkbox for the field (see
        # Postscript tab for examples), meaning that if the field is unchecked,
        # it is assumed that the user doesn't want to set an explicit value. If
        # the field is checked, the actual checkbox can be either checked or
        # not.
        self.assertFalse(attrEdit.isTristate())

        attrEdit.setCheckState(Qt.Checked)
        self.fontInfo.accept()
        value = attrEdit.checkState()
        self.assertEqual(value, Qt.Checked)
        self.assertEqual(getattr(self.font.info, attrName), True)

        attrEdit.setCheckState(Qt.Unchecked)
        self.fontInfo.accept()
        value = attrEdit.checkState()
        self.assertEqual(value, Qt.Unchecked)
        self.assertEqual(getattr(self.font.info, attrName), False)

        attrEdit.setEnabled(False)
        self.fontInfo.accept()
        self.assertIsNone(getattr(self.font.info, attrName))


class GeneralTabTest(TabTestCase):

    def __init__(self, methodName):
        super().__init__(methodName)

    def setUp(self):
        super().setUp()
        self.tab = self.generalTab

    def test_GeneralTab_name(self):
        self.assertEqual(self.tab.name, "General")

    def test_familyName(self):
        self.checkString("familyName")

    def test_styleName(self):
        self.checkString("styleName")

    # TODO styleMapFamilyName, ...DateCreated

    def test_versionMajor(self):
        self.checkInteger("versionMajor")

    def test_versionMinor(self):
        self.checkPositiveInteger("versionMinor")

    def test_unitsPerEm(self):
        self.checkPositiveIntegerFloat("unitsPerEm", value=1000)

    def test_italicAngle(self):
        self.checkIntegerFloat("italicAngle")

    def test_ascender(self):
        self.checkIntegerFloat("ascender", 750)

    def test_descender(self):
        self.checkIntegerFloat("descender", -250)

    def test_capHeight(self):
        self.checkIntegerFloat("capHeight", 700)

    def test_xHeight(self):
        self.checkIntegerFloat("xHeight", 500)

    def test_noteEdit(self):
        self.checkMultilineString("note")


class LegalTabTest(TabTestCase):

    def __init__(self, methodName):
        super().__init__(methodName)

    def setUp(self):
        super().setUp()
        self.tab = self.legalTab

    def test_MetricsTab_name(self):
        self.assertEqual(self.tab.name, "Legal")

    def test_designer(self):
        self.checkString("openTypeNameDesigner")

    def test_designerURL(self):
        self.checkString("openTypeNameDesignerURL")

    def test_manufacturer(self):
        self.checkString("openTypeNameManufacturer")

    def test_manufacturerURL(self):
        self.checkString("openTypeNameManufacturerURL")

    def test_copyright(self):
        self.checkMultilineString("copyright")

    def test_license(self):
        self.checkMultilineString("openTypeNameLicense")

    def test_licenseURL(self):
        self.checkString("openTypeNameLicenseURL")

    def test_trademark(self):
        self.checkString("trademark")


class OpenTypeTabTest(TabTestCase):

    def __init__(self, methodName):
        super().__init__(methodName)

    def setUp(self):
        super().setUp()
        self.tab = self.openTypeTab

    def test_OpenTypeTab_name(self):
        self.assertEqual(self.tab.name, "OpenType")

    def test_lowestRecPPEM(self):
        self.checkPositiveInteger("openTypeHeadLowestRecPPEM")

    # TODO: head flags

    def test_preferredFamilyName(self):
        self.checkString("openTypeNamePreferredFamilyName")

    def test_preferredSubfamilyName(self):
        self.checkString("openTypeNamePreferredSubfamilyName")

    def test_compatibleFullName(self):
        self.checkString("openTypeNameCompatibleFullName")

    def test_WWSFamilyName(self):
        self.checkString("openTypeNameWWSFamilyName")

    def test_WWSSubfamilyName(self):
        self.checkString("openTypeNameWWSSubfamilyName")

    def test_version(self):
        self.checkString("openTypeNameVersion")

    def test_uniqueID(self):
        self.checkString("openTypeNameUniqueID")

    def test_description(self):
        self.checkString("openTypeNameDescription")

    def test_sampleText(self):
        self.checkString("openTypeNameSampleText")

    # TODO: name records table

    def test_ascender(self):
        self.checkInteger("openTypeHheaAscender")

    def test_descender(self):
        self.checkInteger("openTypeHheaDescender")

    def test_lineGap(self):
        self.checkInteger("openTypeHheaLineGap")

    def test_caretSlopeRise(self):
        self.checkInteger("openTypeHheaCaretSlopeRise")

    def test_caretSlopeRun(self):
        self.checkInteger("openTypeHheaCaretSlopeRun")

    def test_caretOffset(self):
        self.checkInteger("openTypeHheaCaretOffset")

    def test_vertTypoAscender(self):
        self.checkInteger("openTypeVheaVertTypoAscender")

    def test_vertTypoDescender(self):
        self.checkInteger("openTypeVheaVertTypoDescender")

    def test_vertTypoLineGap(self):
        self.checkInteger("openTypeVheaVertTypoLineGap")

    def test_vheaCaretSlopeRise(self):
        self.checkInteger("openTypeVheaCaretSlopeRise")

    def test_vheaCaretSlopeRun(self):
        self.checkInteger("openTypeVheaCaretSlopeRun")

    def test_vheaCaretOffset(self):
        self.checkInteger("openTypeVheaCaretOffset")

    # TODO: test_achVendorID()

    # TODO: test_usWidthClass(), test_usWeightClass()

    # TODO: test_fsSelection()

    # TODO: fsType

    # TODO: Panose

    # TODO: ulUnicodeRange, ulCodePageRange

    def test_sTypoAscender(self):
        self.checkInteger("openTypeOS2TypoAscender")

    def test_sTypoDescender(self):
        self.checkInteger("openTypeOS2TypoDescender")

    def test_sTypoLineGap(self):
        self.checkInteger("openTypeOS2TypoLineGap")

    def test_usWinAscent(self):
        self.checkPositiveInteger("openTypeOS2WinAscent")

    def test_usWinDescent(self):
        self.checkPositiveInteger("openTypeOS2WinDescent")

    def test_ySubscriptXSize(self):
        self.checkInteger("openTypeOS2SubscriptXSize")

    def test_ySubscriptYSize(self):
        self.checkInteger("openTypeOS2SubscriptYSize")

    def test_ySubscriptXOffset(self):
        self.checkInteger("openTypeOS2SubscriptXOffset")

    def test_ySubscriptYOffset(self):
        self.checkInteger("openTypeOS2SubscriptYOffset")

    def test_ySuperscriptXSize(self):
        self.checkInteger("openTypeOS2SuperscriptXSize")

    def test_ySuperscriptYSize(self):
        self.checkInteger("openTypeOS2SuperscriptYSize")

    def test_ySuperscriptXOffset(self):
        self.checkInteger("openTypeOS2SuperscriptXOffset")

    def test_ySuperscriptYOffset(self):
        self.checkInteger("openTypeOS2SuperscriptYOffset")

    def test_yStrikeoutSize(self):
        self.checkInteger("openTypeOS2StrikeoutSize")

    def test_yStrikeoutPosition(self):
        self.checkInteger("openTypeOS2StrikeoutPosition")


class PostScriptTabTest(TabTestCase):

    def __init__(self, methodName):
        super().__init__(methodName)

    def setUp(self):
        super().setUp()
        self.tab = self.postScriptTab

    def test_PostScriptTab_name(self):
        self.assertEqual(self.tab.name, "PostScript")

    def test_fontName(self):
        self.checkString("postscriptFontName")

    def test_fullName(self):
        self.checkString("postscriptFullName")

    def test_weightName(self):
        self.checkString("postscriptWeightName")

    def test_uniqueID(self):
        # XXX: Range?
        self.checkInteger("postscriptUniqueID")

    def test_blueValues(self):
        self.checkIntegerFloatList("postscriptBlueValues")

    def test_otherBlues(self):
        self.checkIntegerFloatList("postscriptOtherBlues")

    def test_familyBlues(self):
        self.checkIntegerFloatList("postscriptFamilyBlues")

    def test_familyOtherBlues(self):
        self.checkIntegerFloatList("postscriptFamilyOtherBlues")

    def test_stemSnapH(self):
        self.checkIntegerFloatList("postscriptStemSnapH")

    def test_stemSnapV(self):
        self.checkIntegerFloatList("postscriptStemSnapV")

    def test_blueFuzz(self):
        self.checkIntegerFloat("postscriptBlueFuzz")

    def test_blueScale(self):
        self.checkIntegerFloat("postscriptBlueScale")

    def test_blueShift(self):
        self.checkIntegerFloat("postscriptBlueShift")

    def test_forceBold(self):
        self.checkBoolean("postscriptForceBold")

    def test_defaultWidthX(self):
        self.checkIntegerFloat("postscriptDefaultWidthX")

    def test_nominalWidthX(self):
        self.checkIntegerFloat("postscriptNominalWidthX")

    def test_underlineThickness(self):
        self.checkIntegerFloat("postscriptUnderlineThickness")

    def test_underlinePosition(self):
        self.checkIntegerFloat("postscriptUnderlinePosition")

    def test_slantAngle(self):
        self.checkIntegerFloat("postscriptSlantAngle")

    def test_isFixedPitch(self):
        self.checkBoolean("postscriptIsFixedPitch")

    def test_defaultCharacter(self):
        self.checkString("postscriptDefaultCharacter")

    # TODO: test_windowsCharacterSet


if __name__ == "__main__":
    unittest.main()
