from PyQt5.QtCore import QFile, QRegExp, Qt
from PyQt5.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMainWindow, QMenu,
        QMessageBox, QTextEdit)

class MainEditWindow(QMainWindow):
    def __init__(self, features=None, parent=None):
        super(MainEditWindow, self).__init__(parent)

        self.features = features
        self.setupFileMenu()
#        self.setupHelpMenu()
        self.editor = TextEditor(features.text, self)
        self.resize(600,500)

        self.setCentralWidget(self.editor)
        self.setWindowTitle("Font features")

    def about(self):
        QMessageBox.about(self, "About Syntax Highlighter",
                "<p>The <b>Syntax Highlighter</b> example shows how to " \
                "perform simple syntax highlighting by subclassing the " \
                "QSyntaxHighlighter class and describing highlighting " \
                "rules using regular expressions.</p>")

    def newFile(self):
        self.editor.clear()

    def openFile(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Open File", '',
                    "C++ Files (*.cpp *.h)")

        if path:
            inFile = QFile(path)
            if inFile.open(QFile.ReadOnly | QFile.Text):
                text = inFile.readAll()

                try:
                    # Python v3.
                    text = str(text, encoding='ascii')
                except TypeError:
                    # Python v2.
                    text = str(text)

                self.editor.setPlainText(text)

    def save(self):
        self.editor.write(self.features)

    def setupFileMenu(self):
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

#        fileMenu.addAction("&New...", self.newFile, "Ctrl+N")
#        fileMenu.addAction("&Open...", self.openFile, "Ctrl+O")
        fileMenu.addAction("&Save...", self.save, "Ctrl+S")
        fileMenu.addAction("E&xit", QApplication.instance().quit, "Ctrl+Q")

    def setupHelpMenu(self):
        helpMenu = QMenu("&Help", self)
        self.menuBar().addMenu(helpMenu)

        helpMenu.addAction("&About", self.about)
        helpMenu.addAction("About &Qt", QApplication.instance().aboutQt)

class TextEditor(QTextEdit):
    def __init__(self, text=None, parent=None):
        super(TextEditor, self).__init__(parent)
        font = QFont()
        font.setFamily('CamingoCode')
        font.setPointSize(10)
        font.setFixedPitch(True)

        self.setAcceptRichText(False)
        self.setPlainText(text)
        self.setFont(font)

        self.highlighter = Highlighter(self.document())
    
    def setFontParams(self, family='CamingoCode', ptSize=10, isMono=True):
        font = QFont()
        font.setFamily(family)
        font.setPointSize(ptSize)
        font.setFixedPitch(isMono)
        self.setFont(font)

    def write(self, features):
        features.text = self.toPlainText()

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(200,50,150))
        keywordFormat.setFontWeight(QFont.Bold)

        keywordPatterns = ["\\bAscender\\b", "\\bAttach\\b", "\\bCapHeight\\b", "\\bCaretOffset\\b", "\\bCodePageRange\\b",
            "\\bDescender\\b", "\\bFontRevision\\b", "\\bGlyphClassDef\\b", "\\bHorizAxis.BaseScriptList\\b",
            "\\bHorizAxis.BaseTagList\\b", "\\bHorizAxis.MinMax\\b", "\\bIgnoreBaseGlyphs\\b", "\\bIgnoreLigatures\\b",
            "\\bIgnoreMarks\\b", "\\bLigatureCaretByDev\\b", "\\bLigatureCaretByIndex\\b", "\\bLigatureCaretByPos\\b",
            "\\bLineGap\\b", "\\bMarkAttachClass\\b", "\\bMarkAttachmentType\\b", "\\bNULL\\b", "\\bPanose\\b", "\\bRightToLeft\\b",
            "\\bTypoAscender\\b", "\\bTypoDescender\\b", "\\bTypoLineGap\\b", "\\bUnicodeRange\\b", "\\bUseMarkFilteringSet\\b",
            "\\bVendor\\b", "\\bVertAdvanceY\\b", "\\bVertAxis.BaseScriptList\\b", "\\bVertAxis.BaseTagList\\b",
            "\\bVertAxis.MinMax\\b", "\\bVertOriginY\\b", "\\bVertTypoAscender\\b", "\\bVertTypoDescender\\b",
            "\\bVertTypoLineGap\\b", "\\bXHeight\\b", "\\banchorDef\\b", "\\banchor\\b", "\\banonymous\\b", "\\banon\\b",
            "\\bby\\b", "\\bcontour\\b", "\\bcursive\\b", "\\bdevice\\b", "\\benumerate\\b", "\\benum\\b", "\\bexclude_dflt\\b",
            "\\bfeatureNames\\b", "\\bfeature\\b", "\\bfrom\\b", "\\bignore\\b", "\\binclude_dflt\\b", "\\binclude\\b",
            "\\blanguagesystem\\b", "\\blanguage\\b", "\\blookupflag\\b", "\\blookup\\b", "\\bmarkClass\\b", "\\bmark\\b",
            "\\bnameid\\b", "\\bname\\b", "\\bparameters\\b", "\\bposition\\b", "\\bpos\\b", "\\brequired\\b", "\\breversesub\\b",
            "\\brsub\\b", "\\bscript\\b", "\\bsizemenuname\\b", "\\bsubstitute\\b", "\\bsubtable\\b", "\\bsub\\b", "\\btable\\b",
            "\\buseExtension\\b", "\\bvalueRecordDef\\b", "\\bwinAscent\\b", "\\bwinDescent\\b"]

        self.highlightingRules = [(QRegExp("(" + "|".join(keywordPatterns) + ")"), keywordFormat)]

        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(Qt.darkGray)
        self.highlightingRules.append((QRegExp("#[^\n]*"),
                singleLineCommentFormat))

        classFormat = QTextCharFormat()
        classFormat.setFontWeight(QFont.Bold)
        classFormat.setForeground(QColor(30,150,220))
        self.highlightingRules.append((QRegExp("@[A-Za-z0-9_.]+"),
                classFormat))
#        self.multiLineCommentFormat = QTextCharFormat()
#        self.multiLineCommentFormat.setForeground(Qt.red)

#        quotationFormat = QTextCharFormat()
#        quotationFormat.setForeground(Qt.darkGreen)
#        self.highlightingRules.append((QRegExp("\".*\""), quotationFormat))

#        functionFormat = QTextCharFormat()
#        functionFormat.setFontItalic(True)
#        functionFormat.setForeground(Qt.blue)
#        self.highlightingRules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\()"),
#                functionFormat))

#        self.commentStartExpression = QRegExp("/\\*")
#        self.commentEndExpression = QRegExp("\\*/")

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        '''
        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)

        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()

            self.setFormat(startIndex, commentLength,
                    self.multiLineCommentFormat)
            startIndex = self.commentStartExpression.indexIn(text,
                    startIndex + commentLength);
        '''

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(640, 512)
    window.show()
    sys.exit(app.exec_())
