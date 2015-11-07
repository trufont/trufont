import re

_parseGL_RE = re.compile("([A-Za-z_0-9.]+);([0-9A-F]{4})")


def parseGlyphList(path):
    GL2UV = {}
    with open(path) as file:
        for line in file:
            if not line or line[:1] == '#':
                continue
            m = _parseGL_RE.match(line)
            if not m:
                print("warning: syntax error in glyphlist: %s".format(
                    repr(line[:20])))
            glyphName = m.group(1)
            if glyphName in GL2UV:
                print("warning: glyphName redefined in glyphList: {}".format(
                    glyphName))
            GL2UV[glyphName] = int(m.group(2), 16)
    return GL2UV
