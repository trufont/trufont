import io

# add a clear method?


class TextCursor:
    __slots__ = "_canvas", "_text", "_position", "_anchor"

    def __init__(self, canvas, text):
        self._canvas = canvas
        self._text = text

        self._position = 0
        self._anchor = 0

    @property
    def anchor(self):
        return self._anchor

    @property
    def position(self):
        return self._position

    def deleteChar(self):
        text = self._text
        if self._position >= len(text):
            return
        del text[self._position]
        self._canvas.applyTextChange()

    def deletePreviousChar(self):
        pos = self._position
        if pos <= 0:
            return
        pos -= 1
        del self._text[pos]
        self._position = pos
        self._canvas.applyTextChange()

    def popPreviousChar(self):
        pos = self._position-1
        if pos < 0:
            return
        elem = self._text[pos]
        self.deletePreviousChar()
        font = self._canvas._font
        if elem.startswith("/"):
            if elem == "//":
                index = font.glyphIdForCodepoint(ord("/"))
            else:
                index = font.glyphIdForName(elem[1:])
        else:
            index = font.glyphIdForCodepoint(ord(elem))
        return index

    def insertGlyph(self, glyph):
        unicode_ = glyph.unicode
        if unicode_ is not None:
            elem = chr(int(unicode_, 16))
            if elem == "/":
                elem = "//"
        else:
            elem = f"/{glyph.name}"
        pos = self._position
        self._text[pos:pos] = [elem]
        self._position += 1
        self._canvas.applyTextChange()

    def insertText(self, text):
        content = []
        font = self._canvas._font
        for ch in text:
            if font.glyphIdForCodepoint(ord(ch)) is None:
                continue
            content.append(ch)
        if not content:
            return
        pos = self._position
        self._text[pos:pos] = content
        self._position += len(content)
        self._canvas.applyTextChange()

    def movePosition(self, op, moveAnchor=True, n=1):
        if op == "left":
            pos = self._position - n
            if pos < 0:
                pos = 0
            self._position = pos
            if moveAnchor:
                self._anchor = pos
            # we could elide no-ops
            self._canvas.applyCursorChange()
        elif op == "right":
            pos = self._position + n
            size = len(self._text)
            if pos > size:
                pos = size
            self._position = pos
            if moveAnchor:
                self._anchor = pos
            # we could elide no-ops
            self._canvas.applyCursorChange()
        else:
            raise ValueError("unknown operation: %r" % op)

    def setPosition(self, pos, moveAnchor=True):
        self._position = pos
        if moveAnchor:
            self._anchor = pos
        # we could elide no-ops
        self._canvas.applyCursorChange()

    def text(self):
        buf = io.StringIO()
        addSpace = False
        for name in self._text:
            if name.startswith("/"):
                addSpace = True
            elif addSpace:
                buf.write(" ")
                addSpace = False
            buf.write(name)
        return buf.getvalue()

    def setText(self, text):
        buf = []
        slash = 0
        for i, ch in enumerate(text):
            if slash > 0:
                if ch == "/" or ch == " ":
                    buf.append(text[slash:i+1])
            elif slash < 0:
                if ch == "/":
                    buf.append("//")
                    slash = 0
                else:
                    slash = -slash
            elif ch == "/":
                slash = -i
            else:
                buf.append(ch)
        if slash > 0:
            buf.append(text[slash:i])
        self._text[:] = buf
        self.setPosition(len(buf))
        self._canvas.applyTextChange()
