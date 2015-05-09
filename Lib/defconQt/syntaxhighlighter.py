from PyQt5.QtCore import QFile, QRegExp, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMainWindow, QMenu,
        QMessageBox, QPlainTextEdit, QWidget)

class MainEditWindow(QMainWindow):
    def __init__(self, font=None, parent=None):
        super(MainEditWindow, self).__init__(parent)

        self.font = font
        self.setupFileMenu()
#        self.setupHelpMenu()
        self.editor = TextEditor(self.font.features.text, self)
        self.resize(600,500)

        self.setCentralWidget(self.editor)
        self.setWindowTitle("Font features", font)
    
    def setWindowTitle(self, title, font=None):
        if font is not None: puts = "%s%s%s%s%s" % (title, " – ", self.font.info.familyName, " ", self.font.info.styleName)
        else: puts = title
        super(MainEditWindow, self).setWindowTitle(puts)

    def save(self):
        self.editor.write(self.features)

    def setupFileMenu(self):
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

#        fileMenu.addAction("&New...", self.newFile, "Ctrl+N")
#        fileMenu.addAction("&Open...", self.openFile, "Ctrl+O")
        fileMenu.addAction("&Save...", self.save, "Ctrl+S")
        fileMenu.addAction("E&xit", self.close, "Ctrl+Q")

class LineNumberArea(QWidget):
    def __init__(self,editor):
        self.codeEditor = editor
        super(LineNumberArea, self).__init__(editor)

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)
        
class TextEditor(QPlainTextEdit):
    def __init__(self, text=None, parent=None):
        super(TextEditor, self).__init__(parent)
        font = QFont()
        font.setFamily('CamingoCode')
        font.setPointSize(10)
        font.setFixedPitch(True)

        self.setPlainText(text)
        self.setFont(font)

        self.highlighter = Highlighter(self.document())
        # TODO: get rid of jitter on opening
        self.lineNumbers = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
    
    def setFontParams(self, family='CamingoCode', ptSize=10, isMono=True):
        font = QFont()
        font.setFamily(family)
        font.setPointSize(ptSize)
        font.setFixedPitch(isMono)
        self.setFont(font)

    def write(self, features):
        features.text = self.toPlainText()
        
    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumbers)
        painter.fillRect(event.rect(), QColor(230, 230, 230))
        d = event.rect().topRight()
        a = event.rect().bottomRight()
        painter.setPen(Qt.darkGray)
        painter.drawLine(d.x(), d.y(), a.x(), a.y())
        painter.setPen(Qt.black)
        painter.setFont(self.font())
        
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber();
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.drawText(4, top, self.lineNumbers.width() - 8, 
                    self.fontMetrics().height(),
                    Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1
    
    def lineNumberAreaWidth(self):
        digits = 1
        top = max(1, self.blockCount())
        while (top >= 10):
            top /= 10
            digits += 1
        return 10 + self.fontMetrics().width('9') * digits
    
    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumbers.scroll(0, dy);
        else:
            self.lineNumbers.update(0, rect.y(), 
                self.lineNumbers.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)
    
    def updateLineNumberAreaWidth(self, newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
    
    def resizeEvent(self, event):
        super(TextEditor, self).resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumbers.setGeometry(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())

    '''
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            content = self.toPlainText()
            cur_pos = self.textCursor().position()
            if (content[cur_pos-1] == "{"):
                #print(content[:cur_pos+1])
                #print(content[cur_pos+1:])
                # Probably does not handle CR properly
                newtext = content[:cur_pos+1] + "    \n" + content[cur_pos+1:]
                #print(newtext)
                self.setPlainText(newtext)
                self.textCursor().setPosition(cur_pos+5)
        else:
            super(TextEditor, self).keyPressEvent(event)
    '''

    def insertSpaces(self, text):
        print(text[-1])

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(30,150,220))
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

        self.highlightingRules = [(QRegExp("%s%s%s" % ("(", "|".join(keywordPatterns), ")")), keywordFormat)]

        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(Qt.darkGray)
        self.highlightingRules.append((QRegExp("#[^\n]*"),
                singleLineCommentFormat))

        classFormat = QTextCharFormat()
        classFormat.setFontWeight(QFont.Bold)
        classFormat.setForeground(QColor(200,50,150))
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
