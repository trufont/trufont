class CharacterSet(object):
    __slots__ = ["_name", "_glyphNames"]

    def __init__(self, glyphNames, name=None):
        self._name = name
        self._glyphNames = glyphNames

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name

    name = property(_get_name, _set_name, doc="Character set name.")

    def _get_glyphNames(self):
        return self._glyphNames

    def _set_glyphNames(self, glyphNames):
        self._glyphNames = glyphNames

    glyphNames = property(_get_glyphNames, _set_glyphNames, doc="List of glyph names.")
