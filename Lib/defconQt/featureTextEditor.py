from PyQt5.QtCore import QFile, QRegExp, Qt
from PyQt5.QtGui import QColor, QFont, QKeySequence, QPainter, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMainWindow, QMenu,
        QMessageBox, QPlainTextEdit, QWidget)

class MainEditWindow(QMainWindow):
    def __init__(self, font=None, parent=None):
        super(MainEditWindow, self).__init__(parent)

        self.font = font
        self.setupFileMenu()
        self.editor = TextEditor(self.font.features.text, self)
        self.resize(600, 500)

        self.setCentralWidget(self.editor)
        self.setWindowTitle("Font features", self.font)
    
    def setWindowTitle(self, title, font):
        if font is not None: puts = "%s%s%s%s%s" % (title, " – ", self.font.info.familyName, " ", self.font.info.styleName)
        else: puts = title
        super(MainEditWindow, self).setWindowTitle(puts)
    
    def closeEvent(self, event):
        if self.editor.document().isModified():
            closeDialog = QMessageBox(QMessageBox.Question, "Me", "Save your changes?",
                  QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, self)
            closeDialog.setInformativeText("Your changes will be lost if you don’t save them.")
            closeDialog.setModal(True)
            ret = closeDialog.exec_()
            if ret == QMessageBox.Save:
                self.save()
                event.accept()
            elif ret == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
    
    def reload(self):
        self.font.reloadFeatures()
        self.editor.setPlainText(self.font.features.text)

    def save(self):
        self.editor.write(self.font.features.text)

    def setupFileMenu(self):
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&Save...", self.save, QKeySequence.Save)
        fileMenu.addSeparator()
        fileMenu.addAction("Reload from UFO", self.reload)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)

    def sizeHint(self):
        return QSize(self.parent().lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.parent().lineNumberAreaPaintEvent(event)
        
class TextEditor(QPlainTextEdit):
    def __init__(self, text=None, parent=None):
        super(TextEditor, self).__init__(parent)
        font = QFont()
        font.setFamily('Roboto Mono')
        font.setPointSize(10)
        font.setFixedPitch(True)

        self._indent = "    "
        self.highlighter = Highlighter(self.document())
        self.lineNumbers = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        
        self.setPlainText(text)
        self.setFont(font)
    
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
        painter.setPen(QColor(100, 100, 100))
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
        # Avoid too frequent geometry changes
        if digits < 3: digits = 3
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
    
    def findLineIndentLevel(self, cursor):
        indent = 0
        cursor.select(QTextCursor.LineUnderCursor)
        lineLength = len(cursor.selectedText()) // len(self._indent)
        cursor.movePosition(QTextCursor.StartOfLine)
        while (lineLength > 0):
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor, len(self._indent))
            if cursor.selectedText() == self._indent:
                indent += 1
            cursor.movePosition(QTextCursor.NoMove)
            lineLength -= 1
        cursor.movePosition(QTextCursor.EndOfLine)
        return indent

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            cursor = self.textCursor()
            indentLvl = self.findLineIndentLevel(cursor)
            newBlock = False

            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
            if cursor.selectedText() == '{':
                # We don't add a closing tag if there is text right below with the same
                # indentation level because in that case the user might just be looking
                # to add a new line
                ok = cursor.movePosition(QTextCursor.Down)
                if ok:
                    downIndentLvl = self.findLineIndentLevel(cursor)
                    cursor.select(QTextCursor.LineUnderCursor)
                    if cursor.selectedText().strip() == '' or downIndentLvl <= indentLvl:
                        newBlock = True
                    cursor.movePosition(QTextCursor.Up)
                else: newBlock = True
                indentLvl += 1

            cursor.select(QTextCursor.LineUnderCursor)
            if newBlock:
                txt = cursor.selectedText().lstrip(" ").split(" ")
                if len(txt) > 1:
                    if len(txt) < 3 and txt[-1][-1] == '{':
                        feature = txt[-1][:-1]
                    else:
                        feature = txt[1]
                else:
                    feature = None
            cursor.movePosition(QTextCursor.EndOfLine)

            super(TextEditor, self).keyPressEvent(event)
            newLineSpace = "".join((self._indent for _ in range(indentLvl)))
            cursor.insertText(newLineSpace)
            if newBlock:
                super(TextEditor, self).keyPressEvent(event)
                newLineSpace = "".join((newLineSpace[:-len(self._indent)], "} ", feature, ";"))
                cursor.insertText(newLineSpace)
                cursor.movePosition(QTextCursor.Up)
                cursor.movePosition(QTextCursor.EndOfLine)
                self.setTextCursor(cursor)
        elif event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText(self._indent)
        elif event.key() == Qt.Key_Backspace:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor,
                  len(self._indent))
            if cursor.selectedText() == self._indent:
                cursor.removeSelectedText()
            else:
                super(TextEditor, self).keyPressEvent(event)
        else:
            super(TextEditor, self).keyPressEvent(event)

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(30, 150, 220))
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
        classFormat.setForeground(QColor(200, 50, 150))
        self.highlightingRules.append((QRegExp("@[A-Za-z0-9_.]+"),
                classFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(640, 512)
    window.show()
    sys.exit(app.exec_())
