from defconQt.baseCodeEditor import CodeEditor, CodeHighlighter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QColor, QFont, QKeySequence, QTextCharFormat,
                         QTextCursor)
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox
import os


# TODO: implement search and replace
class MainEditWindow(QMainWindow):

    def __init__(self, font=None, parent=None):
        super(MainEditWindow, self).__init__(parent)

        self.font = font
        self.font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")
        self.editor = FeatureTextEditor(self.font.features.text, self)
        self.resize(600, 500)

        fileMenu = QMenu("&File", self)
        fileMenu.addAction("&Save…", self.save, QKeySequence.Save)
        fileMenu.addSeparator()
        fileMenu.addAction("&Reload From Disk", self.reload)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)
        self.menuBar().addMenu(fileMenu)

        self.setCentralWidget(self.editor)
        self.setWindowTitle(font=self.font)
        self.editor.modificationChanged.connect(self.setWindowModified)

    def setWindowTitle(self, title="Font Features", font=None):
        if font is not None:
            puts = "[*]%s – %s %s" % (
                title, self.font.info.familyName, self.font.info.styleName)
        else:
            puts = "[*]%s" % title
        super(MainEditWindow, self).setWindowTitle(puts)

    def _fontInfoChanged(self, notification):
        self.setWindowTitle(font=self.font)

    def closeEvent(self, event):
        if self.editor.document().isModified():
            name = QApplication.applicationName()
            closeDialog = QMessageBox(
                QMessageBox.Question,
                name,
                "Save your changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                self
            )
            closeDialog.setInformativeText(
                "Your changes will be lost if you don’t save them."
            )
            closeDialog.setModal(True)
            ret = closeDialog.exec_()
            if ret == QMessageBox.Save:
                self.save()
                event.accept()
            elif ret == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
            self.font.info.removeObserver(self, "Info.Changed")

    def reload(self):
        self.font.reloadFeatures()
        self.editor.setPlainText(self.font.features.text)

    def save(self):
        self.editor.write(self.font.features)


class FeatureTextEditor(CodeEditor):

    def __init__(self, text=None, parent=None):
        super(FeatureTextEditor, self).__init__(text, parent)
        self.openBlockDelimiter = '{'
        self.highlighter = FeatureTextHighlighter(self.document())

    def write(self, features):
        features.text = self.toPlainText()
        self.document().setModified(False)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return:
            cursor = self.textCursor()
            indentLvl = self.findLineIndentLevel()
            newBlock = False

            pos = cursor.position()
            cursor.movePosition(QTextCursor.PreviousCharacter,
                                QTextCursor.KeepAnchor)
            if cursor.selectedText() == self.openBlockDelimiter:
                # We don't add a closing tag if there is text right
                # below with the same indentation level because in
                # that case the user might just be looking to add a
                # new line
                ok = cursor.movePosition(QTextCursor.Down)
                if ok:
                    downIndentLvl = self.findLineIndentLevel(cursor)
                    cursor.select(QTextCursor.LineUnderCursor)
                    if (cursor.selectedText().strip() == ''
                            or downIndentLvl <= indentLvl):
                        newBlock = True
                    cursor.movePosition(QTextCursor.Up)
                else:
                    newBlock = True
                indentLvl += 1

            if newBlock:
                cursor.select(QTextCursor.LineUnderCursor)
                txt = cursor.selectedText().lstrip(" ").split(" ")
                if len(txt) > 1:
                    if len(txt) < 3 and txt[-1][-1] == self.openBlockDelimiter:
                        feature = txt[-1][:-1]
                    else:
                        feature = txt[1]
                else:
                    feature = None
            cursor.setPosition(pos)

            cursor.insertText("\n")
            newLineSpace = "".join(self.indent for _ in range(indentLvl))
            cursor.insertText(newLineSpace)
            if newBlock:
                cursor.insertText("\n")
                newLineSpace = "".join((newLineSpace[:-len(self.indent)], "} ",
                                        feature, ";"))
                cursor.insertText(newLineSpace)
                cursor.movePosition(QTextCursor.Up)
                cursor.movePosition(QTextCursor.EndOfLine)
                self.setTextCursor(cursor)
        else:
            super(FeatureTextEditor, self).keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.source() != self:
            mimeData = event.mimeData()
            if mimeData.hasUrls():
                paths = mimeData.urls()
                for path in paths:
                    localPath = path.toLocalFile()
                    if os.path.splitext(localPath)[1] == ".fea":
                        event.acceptProposedAction()
                        break
                return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.source() != self:
            mimeData = event.mimeData()
            if mimeData.hasUrls():
                paths = mimeData.urls()
                feaPaths = []
                for path in paths:
                    localPath = path.toLocalFile()
                    if os.path.splitext(localPath)[1] == ".fea":
                        feaPaths.append(localPath)
                textCursor = self.cursorForPosition(event.pos())
                textCursor.insertText("\n".join(
                    "include(%s);" % feaPath for feaPath in feaPaths))
                self.setTextCursor(textCursor)
                # XXX: Qt uses cleanup routines in a private namespace
                # called by the superclass. Ugh. We have no choice but to make
                # up an empty event if we want to exit drag state.
                mimeData = mimeData.__class__()
                event = event.__class__(
                    event.posF(), event.possibleActions(), mimeData,
                    event.mouseButtons(), event.keyboardModifiers())
        super().dropEvent(event)

keywordPatterns = [
    "Ascender", "Attach", "CapHeight", "CaretOffset", "CodePageRange",
    "Descender", "FontRevision", "GlyphClassDef", "HorizAxis.BaseScriptList",
    "HorizAxis.BaseTagList", "HorizAxis.MinMax", "IgnoreBaseGlyphs",
    "IgnoreLigatures", "IgnoreMarks", "LigatureCaretByDev",
    "LigatureCaretByIndex", "LigatureCaretByPos", "LineGap", "MarkAttachClass",
    "MarkAttachmentType", "NULL", "Panose", "RightToLeft", "TypoAscender",
    "TypoDescender", "TypoLineGap", "UnicodeRange", "UseMarkFilteringSet",
    "Vendor", "VertAdvanceY", "VertAxis.BaseScriptList",
    "VertAxis.BaseTagList", "VertAxis.MinMax", "VertOriginY",
    "VertTypoAscender", "VertTypoDescender", "VertTypoLineGap", "XHeight",
    "anchorDef", "anchor", "anonymous", "anon", "by", "contour", "cursive",
    "device", "enumerate", "enum", "exclude_dflt", "featureNames", "feature",
    "from", "ignore", "include_dflt", "include", "languagesystem", "language",
    "lookupflag", "lookup", "markClass", "mark", "nameid", "name",
    "parameters", "position", "pos", "required", "reversesub", "rsub",
    "script", "sizemenuname", "substitute", "subtable", "sub", "table",
    "useExtension", "valueRecordDef", "winAscent", "winDescent"
]


class FeatureTextHighlighter(CodeHighlighter):

    def __init__(self, parent=None):
        super(FeatureTextHighlighter, self).__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(34, 34, 34))
        keywordFormat.setFontWeight(QFont.Bold)
        self.highlightingRules.append(("\\b(%s)\\b"
                                       % ("|".join(keywordPatterns)),
                                       keywordFormat))

        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(Qt.darkGray)
        self.highlightingRules.append(("#[^\n]*", singleLineCommentFormat))

        groupFormat = QTextCharFormat()
        groupFormat.setFontWeight(QFont.Bold)
        groupFormat.setForeground(QColor(96, 106, 161))
        self.highlightingRules.append(("@[A-Za-z0-9_.]+", groupFormat))
