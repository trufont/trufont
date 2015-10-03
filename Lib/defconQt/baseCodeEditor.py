from PyQt5.QtCore import QRegularExpression, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QSyntaxHighlighter, QTextCursor
from PyQt5.QtWidgets import QPlainTextEdit, QWidget

# maybe add closeEvent

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)

    def sizeHint(self):
        return QSize(self.parent().lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.parent().lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, text=None, parent=None):
        super(CodeEditor, self).__init__(parent)
        # https://gist.github.com/murphyrandle/2921575
        font = QFont('Roboto Mono', 10)
        font.setFixedPitch(True)
        self.setFont(font)

        self.indent = "    "
        self.openBlockDelimiter = None
        self.lineNumbers = LineNumberArea(self)
        self.setPlainText(text)
        # kick-in geometry update before arming signals bc blockCountChanged
        # won't initially trigger if text is None or one-liner.
        self.updateLineNumberAreaWidth()
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)

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
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.drawText(4, top, self.lineNumbers.width() - 8,
                    self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def lineNumberAreaWidth(self):
        digits = 1
        top = max(1, self.blockCount())
        while top >= 10:
            top /= 10
            digits += 1
        # Avoid too frequent geometry changes
        if digits < 3: digits = 3
        return 10 + self.fontMetrics().width('9') * digits

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumbers.scroll(0, dy)
        else:
            self.lineNumbers.update(0, rect.y(), self.lineNumbers.width(),
                rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def updateLineNumberAreaWidth(self, newBlockCount=None):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def resizeEvent(self, event):
        super(CodeEditor, self).resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumbers.setGeometry(cr.left(), cr.top(),
            self.lineNumberAreaWidth(), cr.height())

    def findLineIndentLevel(self, cursor):
        indent = 0
        cursor.select(QTextCursor.LineUnderCursor)
        lineLength = len(cursor.selectedText()) // len(self.indent)
        cursor.movePosition(QTextCursor.StartOfLine)
        while lineLength > 0:
            cursor.movePosition(QTextCursor.NextCharacter,
                QTextCursor.KeepAnchor, len(self.indent))
            if cursor.selectedText() == self.indent:
                indent += 1
            else: break
            # Now move the anchor back to the position()
            #cursor.movePosition(QTextCursor.NoMove) # shouldn't NoMove work here?
            cursor.setPosition(cursor.position())
            lineLength -= 1
        cursor.movePosition(QTextCursor.EndOfLine)
        return indent

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return:
            cursor = self.textCursor()
            indentLvl = self.findLineIndentLevel(cursor)
            if self.openBlockDelimiter is not None:
                cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
                if cursor.selectedText() == self.openBlockDelimiter:
                    indentLvl += 1
            super(CodeEditor, self).keyPressEvent(event)
            newLineSpace = "".join(self.indent for _ in range(indentLvl))
            cursor = self.textCursor()
            cursor.insertText(newLineSpace)
        elif key == Qt.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText(self.indent)
        elif key == Qt.Key_Backspace:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor,
                  len(self.indent))
            if cursor.selectedText() == self.indent:
                cursor.removeSelectedText()
            else:
                super(CodeEditor, self).keyPressEvent(event)
        else:
            super(CodeEditor, self).keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            font = self.font()
            newPointSize = font.pointSize() + event.angleDelta().y() / 120.0
            event.accept()
            if newPointSize < 6: return
            font.setPointSize(newPointSize)
            self.setFont(font)
        else:
            super(CodeEditor, self).wheelEvent(event)

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(CodeHighlighter, self).__init__(parent)
        self.highlightingRules = []

    def highlightBlock(self, text):
        for pattern, fmt in self.highlightingRules:
            regex = QRegularExpression(pattern)
            i = regex.globalMatch(text)
            while i.hasNext():
                match = i.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)
        self.setCurrentBlockState(0)
