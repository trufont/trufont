"""
The *baseCodeEditor* submodule
------------------------------

The *baseCodeEditor* submodule provides language-agnostic code editor parts,
including a search widget, goto dialog and code highlighter.
"""

import re

from PyQt5.QtCore import QRegularExpression, QSize, Qt, pyqtSignal
from PyQt5.QtGui import (
    QColor,
    QFontMetricsF,
    QPainter,
    QPalette,
    QRegularExpressionValidator,
    QSyntaxHighlighter,
    QTextCursor,
)
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from defconQt.tools import drawing, platformSpecific

__all__ = ["GotoLineDialog", "BaseCodeHighlighter", "BaseCodeEditor"]

# -------------------
# Search/Jump dialogs
# -------------------


# TODO: search widget


class GotoLineDialog(QDialog):
    """
    A QDialog_ that asks for a line:column number to the user. Column number is
    optional.

    The result may be passed to the :func:`scrollToLine` function of
    :class:`BaseCodeEditor`.

    .. _QDialog: http://doc.qt.io/qt-5/qdialog.html
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Go to…"))

        self.lineEdit = QLineEdit(self)
        validator = QRegularExpressionValidator(self)
        validator.setRegularExpression(
            QRegularExpression("(^[1-9][0-9]*(:[1-9][0-9]*)?$)?")
        )
        self.lineEdit.setValidator(validator)
        self.lineEdit.returnPressed.connect(self.accept)
        label = QLabel(self.tr("Enter a row:column to go to"), self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.lineEdit)
        layout.addWidget(label)
        self.setLayout(layout)

    @classmethod
    def getLineColumnNumber(cls, parent):
        dialog = cls(parent)
        result = dialog.exec_()
        newLine = dialog.lineEdit.text()
        if newLine:
            newLine = [int(nb) for nb in newLine.split(":")]
        else:
            newLine = [None]
        if len(newLine) < 2:
            newLine.append(None)
        newLine.append(result)
        return tuple(newLine)


# ------------
# Line numbers
# ------------


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)

    def sizeHint(self):
        return QSize(self.parent().lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.parent().lineNumberAreaPaintEvent(event)


# ----------------
# Syntax highlight
# ----------------


class BaseCodeHighlighter(QSyntaxHighlighter):
    """
    A QSyntaxHighlighter_ that highlights code using QRegularExpression_
    (perl regexes).
    Use :func:`addRule` to add a formatting rule or :func:`addBlockRule` to add a
    rule with start and end patterns (e.g., multiline rules).

    # TODO: get/remove rules?

    .. _QRegularExpression: http://doc.qt.io/qt-5/qregularexpression.html
    .. _QSyntaxHighlighter: http://doc.qt.io/qt-5/qsyntaxhighlighter.html
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blockHighlightingRules = []
        self._highlightingRules = []
        self._visited = set()

    def addBlockRule(self, startPattern, endPattern, textFormat):
        """
        Add a block syntax highlighting rule, that begins with regex string
        *startPattern* and ends with *endPattern* formatted according to
        QTextCharFormat_ *format*.

        .. _QTextCharFormat: http://doc.qt.io/qt-5/qtextcharformat.html
        """
        startRegex = QRegularExpression(startPattern)
        endRegex = QRegularExpression(endPattern)
        self._blockHighlightingRules.append((startRegex, endRegex, textFormat))

    def addRule(self, pattern, textFormat):
        """
        Add a syntax highlighting rule with regex string *pattern* and
        QTextCharFormat_ *format*.

        .. _QTextCharFormat: http://doc.qt.io/qt-5/qtextcharformat.html
        """
        regex = QRegularExpression(pattern)
        self._highlightingRules.append((regex, textFormat))

    def highlightBlock(self, text):
        self._visited = set()
        # reset state, in case an earlier block just toggled
        self.setCurrentBlockState(-1)
        # block patterns
        for ident, rules in enumerate(self._blockHighlightingRules):
            startRegex, endRegex, textFormat = rules

            startIndex = offset = 0
            if self.previousBlockState() != ident:
                match = startRegex.match(text)
                startIndex = match.capturedStart()
                offset = match.capturedLength()

            while startIndex >= 0:
                match = endRegex.match(text, startIndex + offset)
                endIndex = match.capturedStart()
                if endIndex == -1:
                    self.setCurrentBlockState(ident)
                    commentLength = len(text) - startIndex
                else:
                    commentLength = endIndex - startIndex + match.capturedLength()
                self.setFormat(startIndex, commentLength, textFormat)
                match = startRegex.match(text, startIndex + commentLength)
                startIndex = match.capturedStart()
                offset = match.capturedLength()

        # inline patterns
        for regex, textFormat in self._highlightingRules:
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, textFormat)

    def setFormat(self, start, count, *args):
        overlap = False
        for s, e in self._visited:
            if start <= e and s <= start + count:
                overlap = True
        self._visited.add((start, start + count))
        if not overlap:
            super().setFormat(start, count, *args)


# -------------------
# Whitespace Guessing
# -------------------

_whitespaceRE = re.compile("([ \t]+)")


def _guessMinWhitespace(text):
    # gather all whitespace at the beginning of a line
    whitespace = set()
    for line in text.splitlines():
        # skip completely blank lines
        if not line.strip():
            continue
        # store the found whitespace
        m = _whitespaceRE.match(line)
        if m is not None:
            whitespace.add(m.group(1))
    # if nothing was found, fallback to four spaces
    if not whitespace:
        return "    "
    # get the smallest whitespace increment
    whitespace = min(whitespace)
    # if the whitespace starts with a tab, use a single tab
    if whitespace.startswith("\t"):
        return "\t"
    # use what was found
    return whitespace


class BaseCodeEditor(QPlainTextEdit):
    """
    A language-agnostic, abstract code editor. Displays line numbers and
    supports arbitrary indent pattern (Tab/Alt+Tab will add/remove indent,
    Return keeps indent).

    - *indent*: the basic indent pattern. 4-spaces by default.
    - *lineNumbersVisible*: whether line numbers are displayed. True by
      default.
    - *openBlockDelimiter*: a string that indicates a new block. If set, this
      will add an additional level of indent if Return key is pressed after
      such string. None by default.
    - *shouldGuessWhiteSpace*: whether whitespace should be inferred when
      :func:`setPlainText` is called.
    """

    openBlockDelimiter = None
    indentChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(platformSpecific.fixedFont())
        self.setTabWidth(4)
        self._indent = "    "
        self._lineNumbersVisible = True
        self._shouldGuessWhitespace = True

        self.lineNumbers = LineNumberArea(self)
        # kick-in geometry update before arming signals
        self.updateLineNumberAreaWidth()
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)

    # --------------
    # Custom methods
    # --------------

    def indent(self):
        """
        Returns this widget’s indent pattern.
        """
        return self._indent

    def setIndent(self, indent):
        """
        Sets this widget’s atomic indent pattern to the string *indent*.

        The default is four spaces.

        TODO: reindent document?
        """
        if self._indent == indent:
            return
        self._indent = indent
        self.indentChanged.emit(self._indent)

    def tabWidth(self):
        return self._tabWidth

    def setTabWidth(self, value):
        self._tabWidth = value
        self.updateTabWidth()

    def updateTabWidth(self):
        if not hasattr(self, "_tabWidth"):
            return
        fM = QFontMetricsF(self.font())
        pixelWidth = fM.width(" ") * self._tabWidth
        document = self.document()
        opt = document.defaultTextOption()
        opt.setTabStop(pixelWidth)
        document.setDefaultTextOption(opt)

    def lineNumbersVisible(self):
        """
        Returns whether line numbers are displayed.
        """
        return self._lineNumbersVisible

    def setLineNumbersVisible(self, value):
        """
        Sets whether line numbers should be displayed on the left margin.

        The default is true.
        """
        self._lineNumbersVisible = value
        self.lineNumbers.setVisible(value)
        self.updateLineNumberAreaWidth()

    def shouldGuessWhitespace(self):
        """
        Returns whether this widget infers whitespace when text is set.
        """
        return self._shouldGuessWhitespace

    def setShouldGuessWhitespace(self, value):
        """
        Sets whether this widget should infer whitespace when
        :func:`setPlainText` is called.

        The default is true.
        """
        self._shouldGuessWhitespace = value

    def scrollToLine(self, lineNumber, columnNumber=None):
        """
        Scrolls this widget’s viewport to the line *lineNumber* and sets the
        text cursor to that line, at *columnNumber*. If *columnNumber* is None,
        bookkeeping will be performed.

        Strictly positive numbers are expected.
        """
        lineNumber -= 1
        if columnNumber is None:
            columnNumber = self.textCursor().positionInBlock()
        else:
            columnNumber -= 1
        scrollingUp = lineNumber < self.textCursor().blockNumber()
        # scroll to block
        textBlock = self.document().findBlockByLineNumber(lineNumber)
        newCursor = QTextCursor(textBlock)
        self.setTextCursor(newCursor)
        # make some headroom
        one, two = QTextCursor.Down, QTextCursor.Up
        if scrollingUp:
            one, two = two, one
        for move in (one, one, two, two):
            self.moveCursor(move)
        # address column
        newCursor.movePosition(QTextCursor.NextCharacter, n=columnNumber)
        self.setTextCursor(newCursor)

    # ------------
    # Line numbers
    # ------------

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter()
        painter.begin(self.lineNumbers)
        rect = event.rect()
        painter.fillRect(rect, self.palette().color(QPalette.Base))
        d = rect.topRight()
        a = rect.bottomRight()
        painter.setPen(QColor(150, 150, 150))
        # Alright. Since we just did setPen() w the default color constructor
        # it set the pen to a cosmetic width (of zero), i.e. drawing one pixel
        # regardless of screen density.
        # The thing is, we want to paint the last pixels at width boundary.
        # So if devicePixelRatio is e.g. 3 (3 device pixels per screen pixel),
        # then we need to translate by 3-1 pixels, but since 3 device pixels
        # is just one pixel is painter units, we'd have to divide by device
        # pixels after, so we would translate by 2/3 "software" pixels.
        pixelRatio = self.lineNumbers.devicePixelRatio()
        delta = (pixelRatio - 1) / pixelRatio
        drawing.drawLine(painter, d.x() + delta, d.y(), a.x() + delta, a.y())
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.drawText(
                    4,
                    top,
                    self.lineNumbers.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1
        painter.end()

    def lineNumberAreaWidth(self):
        if not self._lineNumbersVisible:
            return 0
        digits = 1
        top = max(1, self.blockCount())
        while top >= 10:
            top /= 10
            digits += 1
        # Avoid too frequent geometry changes
        if digits < 3:
            digits = 3
        return 10 + self.fontMetrics().width("9") * digits

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumbers.scroll(0, dy)
        else:
            self.lineNumbers.update(
                0, rect.y(), self.lineNumbers.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def updateLineNumberAreaWidth(self, newBlockCount=None):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumbers.setGeometry(
            cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()
        )

    # ------------
    # Autocomplete
    # ------------

    def findLineIndentLevel(self, cursor=None):
        if cursor is None:
            cursor = self.textCursor()
        indent = 0
        cursor.select(QTextCursor.LineUnderCursor)
        lineLength = len(cursor.selectedText()) // len(self._indent)
        cursor.movePosition(QTextCursor.StartOfLine)
        while lineLength > 0:
            cursor.movePosition(
                QTextCursor.NextCharacter, QTextCursor.KeepAnchor, len(self._indent)
            )
            if cursor.selectedText() == self._indent:
                indent += 1
            else:
                break
            # Now move the anchor back to the position()
            # shouldn't NoMove work here?
            # cursor.movePosition(QTextCursor.NoMove)
            cursor.setPosition(cursor.position())
            lineLength -= 1
        cursor.movePosition(QTextCursor.EndOfLine)
        return indent

    def performLinewiseIndent(self, cursor, positive=True):
        # do a lisewise indent
        p = cursor.position()
        a = cursor.anchor()
        if a > p:
            a, p = p, a

        cursor.setPosition(p)
        pBlock = cursor.blockNumber()
        cursor.setPosition(a)
        aBlock = cursor.blockNumber()

        cursor.beginEditBlock()
        for _ in range(pBlock - aBlock + 1):
            cursor.movePosition(QTextCursor.StartOfBlock)
            if positive:
                cursor.insertText(self._indent)
            else:
                cursor.movePosition(
                    QTextCursor.NextCharacter, QTextCursor.KeepAnchor, len(self._indent)
                )
                if cursor.selectedText() == self._indent:
                    cursor.removeSelectedText()
            cursor.movePosition(QTextCursor.NextBlock)
        cursor.endEditBlock()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return:
            cursor = self.textCursor()
            indentLvl = self.findLineIndentLevel()
            if self.openBlockDelimiter is not None:
                cursor.movePosition(
                    QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor
                )
                if cursor.selectedText() == self.openBlockDelimiter:
                    indentLvl += 1
            super().keyPressEvent(event)
            newLineSpace = "".join(self._indent for _ in range(indentLvl))
            cursor = self.textCursor()
            cursor.insertText(newLineSpace)
        elif key in (Qt.Key_Backspace, Qt.Key_Backtab):
            cursor = self.textCursor()
            if key == Qt.Key_Backtab and cursor.hasSelection():
                self.performLinewiseIndent(cursor, False)
            else:
                cursor.movePosition(
                    QTextCursor.PreviousCharacter,
                    QTextCursor.KeepAnchor,
                    len(self._indent),
                )
                if cursor.selectedText() == self._indent:
                    cursor.removeSelectedText()
                else:
                    super().keyPressEvent(event)
        elif key == Qt.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self.performLinewiseIndent(cursor)
            else:
                cursor.insertText(self._indent)
        else:
            super().keyPressEvent(event)

    # --------------
    # Other builtins
    # --------------

    def setFont(self, font):
        super().setFont(font)
        self.updateTabWidth()

    def setPlainText(self, text):
        super().setPlainText(text)
        if self._shouldGuessWhitespace and text is not None:
            indent = _guessMinWhitespace(text)
            self.setIndent(indent)

    def wheelEvent(self, event):
        if event.modifiers() & platformSpecific.scaleModifier():
            font = self.font()
            newPointSize = font.pointSize() + event.angleDelta().y() / 120.0
            if newPointSize < 6:
                return
            font.setPointSize(newPointSize)
            self.setFont(font)
        else:
            super().wheelEvent(event)
