def characterToGlyphName(c, cmap):
    v = ord(c)
    v = cmap.get(v)
    if isinstance(v, list):
        v = v[0]
    return v


def compileStack(glyphNames, stack):
    if stack:
        glyphNames.append("".join(stack))


def escapeText(text):
    return text.replace("//", "/slash ")


def splitText(
    text,
    cmap,
    fallback=".notdef",
    cmapFunc=characterToGlyphName,
    compileFunc=compileStack,
    escapeFunc=escapeText,
):
    """
    Break a string of characters or / delimited glyph names
    into a list.
    """
    # escape
    text = escapeFunc(text)
    #
    glyphNames = []
    compileStack = None
    for c in text:
        # start a glyph name compile.
        if c == "/":
            # finishing a previous compile.
            if compileStack is not None:
                # only add the compile if something has been added to the stack.
                compileFunc(glyphNames, compileStack)
            # reset the stack.
            compileStack = []
        # adding to or ending a glyph name compile.
        elif compileStack is not None:
            # space. conclude the glyph name compile.
            if c == " ":
                # only add the compile if something has been added to the stack.
                compileFunc(glyphNames, compileStack)
                compileStack = None
            # add the character to the stack.
            else:
                compileStack.append(c)
        # adding a character that needs to be converted to a glyph name.
        else:
            glyphName = cmapFunc(c, cmap)
            if glyphName is None:
                glyphName = fallback
            glyphNames.append(glyphName)
    # catch remaining compile.
    compileFunc(glyphNames, compileStack)
    return glyphNames
