"""
The *featureCodeEditor* submodule
---------------------------------

The *featureCodeEditor* submodule provides an Adobe `feature file`_ code editor,
and a corresponding syntax highlighter.

.. _`feature file`: http://www.adobe.com/devnet/opentype/afdko/topic_feature_file_syntax.html
"""

import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor

from defconQt.controls.baseCodeEditor import BaseCodeEditor, BaseCodeHighlighter

# TODO: maybe move to tools/.
keywordPatterns = [
    "Ascender",
    "Attach",
    "CapHeight",
    "CaretOffset",
    "CodePageRange",
    "Descender",
    "FontRevision",
    "GlyphClassDef",
    "HorizAxis.BaseScriptList",
    "HorizAxis.BaseTagList",
    "HorizAxis.MinMax",
    "IgnoreBaseGlyphs",
    "IgnoreLigatures",
    "IgnoreMarks",
    "LigatureCaretByDev",
    "LigatureCaretByIndex",
    "LigatureCaretByPos",
    "LineGap",
    "MarkAttachClass",
    "MarkAttachmentType",
    "NULL",
    "Panose",
    "RightToLeft",
    "TypoAscender",
    "TypoDescender",
    "TypoLineGap",
    "UnicodeRange",
    "UseMarkFilteringSet",
    "Vendor",
    "VertAdvanceY",
    "VertAxis.BaseScriptList",
    "VertAxis.BaseTagList",
    "VertAxis.MinMax",
    "VertOriginY",
    "VertTypoAscender",
    "VertTypoDescender",
    "VertTypoLineGap",
    "XHeight",
    "anchorDef",
    "anchor",
    "anonymous",
    "anon",
    "by",
    "contour",
    "cursive",
    "device",
    "enumerate",
    "enum",
    "exclude_dflt",
    "featureNames",
    "feature",
    "from",
    "ignore",
    "include_dflt",
    "include",
    "languagesystem",
    "language",
    "lookupflag",
    "lookup",
    "markClass",
    "mark",
    "nameid",
    "name",
    "parameters",
    "position",
    "pos",
    "required",
    "reversesub",
    "rsub",
    "script",
    "sizemenuname",
    "substitute",
    "subtable",
    "sub",
    "table",
    "useExtension",
    "valueRecordDef",
    "winAscent",
    "winDescent",
]


class FeatureCodeHighlighter(BaseCodeHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(45, 95, 235))
        self.addRule("\\b(?<!\\\\)(%s)\\b" % ("|".join(keywordPatterns)), keywordFormat)

        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(QColor(112, 128, 144))
        self.addRule("#[^\n]*", singleLineCommentFormat)

        groupFormat = QTextCharFormat()
        groupFormat.setForeground(QColor(255, 27, 147))
        self.addRule("@[A-Za-z0-9_.]+", groupFormat)


class FeatureCodeEditor(BaseCodeEditor):
    """
    An Adobe feature file code editor.

    Inherits from :class:`BaseCodeEditor` and provides additional,
    language-specific autocompletion.

    Dropping an FEA file on the widget will create an include(...) directive
    that calls to that file.

    # TODO: maybe insert end block when typing open block, not on newline
    + symetric autocomplete for {} like in the py editor
    """

    openBlockDelimiter = "{"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = FeatureCodeHighlighter(self.document())

    def write(self, features):
        """
        TODO: maybe remove this.
        """
        features.text = self.toPlainText()
        self.document().setModified(False)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return:
            cursor = self.textCursor()
            indentLvl = self.findLineIndentLevel()
            newBlock = False

            pos = cursor.position()
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
            if cursor.selectedText() == self.openBlockDelimiter:
                # We don't add a closing tag if there is text right
                # below with the same indentation level because in
                # that case the user might just be looking to add a
                # new line
                ok = cursor.movePosition(QTextCursor.Down)
                if ok:
                    downIndentLvl = self.findLineIndentLevel(cursor)
                    cursor.select(QTextCursor.LineUnderCursor)
                    if (
                        cursor.selectedText().strip() == ""
                        or downIndentLvl <= indentLvl
                    ):
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

            cursor.beginEditBlock()
            cursor.insertText("\n")
            newLineSpace = "".join(self._indent for _ in range(indentLvl))
            cursor.insertText(newLineSpace)
            if newBlock:
                cursor.insertText("\n")
                newLineSpace = "".join(
                    (newLineSpace[: -len(self._indent)], "} ", feature, ";")
                )
                cursor.insertText(newLineSpace)
                cursor.movePosition(QTextCursor.Up)
                cursor.movePosition(QTextCursor.EndOfLine)
                self.setTextCursor(cursor)
            cursor.endEditBlock()
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.source() != self:
            mimeData = event.mimeData()
            if mimeData.hasUrls():
                urls = mimeData.urls()
                for url in urls:
                    if not url.isLocalFile():
                        continue
                    path = url.toLocalFile()
                    if os.path.splitext(path)[1] == ".fea":
                        event.acceptProposedAction()
                        break
                return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.source() != self:
            mimeData = event.mimeData()
            if mimeData.hasUrls():
                urls = mimeData.urls()
                feaPaths = []
                for url in urls:
                    if not url.isLocalFile():
                        continue
                    path = url.toLocalFile()
                    if os.path.splitext(path)[1] == ".fea":
                        feaPaths.append(path)
                textCursor = self.cursorForPosition(event.pos())
                textCursor.insertText(
                    "\n".join("include(%s);" % feaPath for feaPath in feaPaths)
                )
                self.setTextCursor(textCursor)
                # HACK: Qt uses cleanup routines in a private namespace
                # called by the superclass. Ugh. We have no choice but to make
                # up an empty event if we want to exit drag state.
                mimeData = mimeData.__class__()
                event = event.__class__(
                    event.posF(),
                    event.possibleActions(),
                    mimeData,
                    event.mouseButtons(),
                    event.keyboardModifiers(),
                )
        super().dropEvent(event)
