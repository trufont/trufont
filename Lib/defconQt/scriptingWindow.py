from defconQt.baseCodeEditor import CodeEditor, CodeHighlighter
from keyword import kwlist
import traceback
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QColor, QFont, QKeySequence, QTextCharFormat, QTextCursor)
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu


class MainScriptingWindow(QMainWindow):

    def __init__(self):
        super(MainScriptingWindow, self).__init__()

        self.editor = PythonEditor(parent=self)
        self.resize(600, 500)

        fileMenu = QMenu("&File", self)
        fileMenu.addAction("&Run…", self.runScript, "Ctrl+R")
        fileMenu.addSeparator()
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)
        self.menuBar().addMenu(fileMenu)

        self.setCentralWidget(self.editor)
        self.setWindowTitle("[*]Untitled.py")
        # arm `undoAvailable` to `setWindowModified`
        self.editor.undoAvailable.connect(self.setWindowModified)

    def runScript(self):
        app = QApplication.instance()
        script = self.editor.toPlainText()
        global_vars = {
            "__builtins__": __builtins__,
            "AllFonts": app.allFonts,
            "CurrentFont": app.currentFont,
            "CurrentGlyph": app.currentGlyph,
            "rootHandle": self,
        }
        try:
            code = compile(script, "<string>", "exec")
            exec(code, global_vars)
        except:
            print(traceback.format_exc())


class PythonEditor(CodeEditor):
    autocomplete = {
        Qt.Key_ParenLeft: "()",
        Qt.Key_BracketLeft: "[]",
        Qt.Key_BraceLeft: "{}",
        Qt.Key_Apostrophe: "''",
        Qt.Key_QuoteDbl: '""',
    }

    def __init__(self, text=None, parent=None):
        super(PythonEditor, self).__init__(text, parent)
        self.openBlockDelimiter = ":"
        self.highlighter = PythonHighlighter(self.document())

    def keyPressEvent(self, event):
        key = event.key()
        if key in self.autocomplete.keys():
            super(PythonEditor, self).keyPressEvent(event)
            cursor = self.textCursor()
            ok = cursor.movePosition(QTextCursor.NextCharacter)
            if not ok:
                cursor.insertText(self.autocomplete[key][-1])
                cursor.movePosition(QTextCursor.PreviousCharacter)
                self.setTextCursor(cursor)
            event.accept()
            return
        elif key == Qt.Key_Backspace:
            cursor = self.textCursor()
            ok = cursor.movePosition(QTextCursor.PreviousCharacter)
            if ok:
                ok = cursor.movePosition(
                    QTextCursor.NextCharacter, QTextCursor.KeepAnchor, 2)
                if ok and cursor.selectedText() in self.autocomplete.values():
                    cursor.removeSelectedText()
                    event.accept()
                    return
        super(PythonEditor, self).keyPressEvent(event)


class PythonHighlighter(CodeHighlighter):

    def __init__(self, parent=None):
        super(PythonHighlighter, self).__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(34, 34, 34))
        keywordFormat.setFontWeight(QFont.Bold)
        self.highlightingRules.append(
            ("\\b(%s)\\b" % ("|".join(kwlist)), keywordFormat))

        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(Qt.darkGray)
        self.highlightingRules.append(("#[^\n]*", singleLineCommentFormat))

        classOrFnNameFormat = QTextCharFormat()
        classOrFnNameFormat.setForeground(QColor(96, 106, 161))
        self.highlightingRules.append(
            ("(?<=\\bclass\\s|def\\s\\b)\\s*(\\w+)", classOrFnNameFormat))

        quotationFormat = QTextCharFormat()
        quotationFormat.setForeground(QColor(223, 17, 68))
        self.highlightingRules.append(
            ("'.*'|[\"]{1,3}.*[\"]{1,3}", quotationFormat))
