import re
from PyQt5.QtWidgets import QApplication

_parseGL_RE = re.compile("([A-Za-z_0-9.]+);([0-9A-F]{4})")


def parseGlyphList(path):
    GL2UV = {}
    with open(path) as file:
        for line in file:
            if not line or line[:1] == '#':
                continue
            m = _parseGL_RE.match(line)
            if not m:
                raise SyntaxError(
                    QApplication.translate(
                        "parseGlyphList",
                        "syntax error in glyphlist: {}").format(
                        repr(line[:20])))
            glyphName = m.group(1)
            if glyphName in GL2UV:
                print(QApplication.translate(
                    "parseGlyphList",
                    "warning: glyphName redefined in glyphList: {}").format(
                    glyphName))
            GL2UV[glyphName] = int(m.group(2), 16)
    return GL2UV
