import uharfbuzz as hb

CH_GID_PREFIX = 0x80000000

# ----------
# Font funcs
# ----------


def _get_nominal_glyph(font, ch, user_data):
    if ch >= CH_GID_PREFIX:
        return ch - CH_GID_PREFIX
    return user_data._font.glyphIdForCodepoint(ch, 0)


def _get_glyph_h_advance(font, gid, user_data):
    glyph = user_data._font._glyphs[gid]
    # XXX: we should store layers, not glyphs
    return glyph.layerForMaster(None).width


def _get_glyph_name_func(font, gid, user_data):
    return user_data._font._glyphs[gid].name


def _get_layout_table(face, tag, tables):
    return tables.get(tag)


class LayoutEngine:
    __slots__ = "_font", "_tables", "_hbFont"

    def __init__(self, font, tables):
        self._font = font
        self._tables = tables
        upem = font.unitsPerEm

        face = hb.Face.create_for_tables(_get_layout_table, tables)
        face.upem = upem
        font = hb.Font.create(face)
        font.scale = (upem, upem)

        funcs = hb.FontFuncs.create()
        funcs.set_nominal_glyph_func(_get_nominal_glyph, self)
        funcs.set_glyph_h_advance_func(_get_glyph_h_advance, self)
        # TODO: vertical advance
        funcs.set_glyph_name_func(_get_glyph_name_func, self)
        font.funcs = funcs

        self._hbFont = font

    @property
    def features(self):
        # XXX: for now we only list GSUB, default script, default language
        return hb.ot_layout_language_get_feature_tags(self._hbFont.face, "GSUB")

    @property
    def font(self):
        return self._font

    @property
    def languages(self):
        # XXX: for now we only list GSUB, default script
        return hb.ot_layout_script_get_language_tags(self._hbFont.face, "GSUB")

    @property
    def scripts(self):
        # XXX: for now we only list GSUB
        return hb.ot_layout_table_get_script_tags(self._hbFont.face, "GSUB")

    # ----------
    # Engine API
    # ----------

    def process(self, text, direction=None, script=None, language=None, features=None):
        # TODO: reuse buffer?
        buf = hb.Buffer.create()
        if not text:
            return buf

        font = self._font
        if isinstance(text, list):
            unicodes = []
            for elem in text:
                escape = elem == "//"
                if not escape and elem.startswith("/"):
                    gid = font.glyphIdForName(elem[1:])
                    if gid is None:
                        continue
                    uni = CH_GID_PREFIX + gid
                else:
                    if escape:
                        elem = "/"
                    uni = ord(elem)
                unicodes.append(uni)
            buf.add_codepoints(unicodes)
        else:
            buf.add_str(text)

        buf.guess_segment_properties()
        if direction is not None:
            buf.direction = direction
        if script is not None:
            buf.script = script
        if language is not None:
            buf.language = language
        hb.shape(self._hbFont, buf, features)

        return buf
