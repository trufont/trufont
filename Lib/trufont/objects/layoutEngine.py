import weakref

from defcon.objects.base import BaseObject
from fontTools.ttLib import TTFont
from ufo2ft.featureCompiler import FeatureCompiler

from defconQt.controls.glyphContextView import GlyphRecord

try:
    from harfbuzz import HARFBUZZ as HB
    import harfbuzz as hb
except ImportError:
    pass

CH_GID_PREFIX = 0x80000000

# ---------
# Factories
# ---------


def _layoutEngineOTLTablesRepresentationFactory(layoutEngine):
    font = layoutEngine.font
    ret = dict()
    glyphOrder = sorted(font.keys())
    if font.features.text:
        otf = TTFont()
        otf.setGlyphOrder(glyphOrder)
        # compile with feaLib + markWriter/kernWriter
        try:
            compiler = FeatureCompiler(font, otf)
            compiler.postProcess = lambda: None
            compiler.compile()
            for name in ("GDEF", "GSUB", "GPOS"):
                if name in otf:
                    table = otf[name].compile(otf)
                    value = hb.Blob.create_for_array(table, HB.MEMORY_MODE_READONLY)
                    ret[name] = value
        except Exception:
            # TODO: handle this in the UI
            import traceback

            print(traceback.format_exc(5))
            # discard tables from incompletely parsed feature text
            ret = dict()
    return ret, glyphOrder


# harfbuzz


def _get_nominal_glyph(font, engine, ch, user_data):
    if ch >= CH_GID_PREFIX:
        return ch - CH_GID_PREFIX

    ufo = engine.font
    glyphName = ufo.unicodeData.glyphNameForUnicode(ch)
    if glyphName is not None:
        try:
            return engine.glyphOrder.index(glyphName)
        except IndexError:
            pass
    return 0


def _get_glyph_h_advance(font, engine, gid, user_data):
    ufo = engine.font
    glyph = ufo[engine.glyphOrder[gid]]
    return glyph.width * font.scale[0] / font.face.upem


def _get_glyph_name_func(font, engine, gid, user_data):
    return engine.glyphOrder[gid]


def _spitLayoutTable(face, tag, layoutTables):
    name = hb.tag_to_string(tag)
    return layoutTables.get(name)


# TODO: what if the source font does not have .notdef, is there a
# fallback gid?


class LayoutEngine(BaseObject):
    changeNotificationName = "LayoutEngine.Changed"
    representationFactories = {
        "TruFont.layoutEngine.tables": dict(
            factory=_layoutEngineOTLTablesRepresentationFactory,
            destructiveNotifications=("LayoutEngine._DestroyCachedTables"),
        )
    }

    def __init__(self, font):
        self._needsInternalUpdate = True
        self._font = weakref.ref(font)
        self._fontFeatures = dict()
        self._glyphOrder = []
        self._hbFont = None
        super().__init__()
        self.beginSelfNotificationObservation()

    @property
    def font(self):
        if self._font is not None:
            return self._font()
        return None

    @property
    def glyphOrder(self):
        return self._glyphOrder

    # --------------
    # Engine Updates
    # --------------

    def _updateEngine(self):
        if not self._needsInternalUpdate:
            return
        ufo = self.font
        layoutTables, self._glyphOrder = self.getRepresentation(
            "TruFont.layoutEngine.tables"
        )

        face = hb.Face.create_for_tables(_spitLayoutTable, layoutTables, None, False)
        font = hb.Font.create(face)
        face.upem = upem = ufo.info.unitsPerEm
        font.scale = (upem, upem)

        funcs = hb.FontFuncs.create(False)
        funcs.set_nominal_glyph_func(_get_nominal_glyph, None, None)
        funcs.set_glyph_h_advance_func(_get_glyph_h_advance, None, None)
        # TODO: vertical advance
        funcs.set_glyph_name_func(_get_glyph_name_func, None, None)
        font.set_funcs(funcs, self, None)

        self._hbFont = font
        self._needsInternalUpdate = False

    # -------------
    # Notifications
    # -------------

    def beginSelfNotificationObservation(self):
        super().beginSelfNotificationObservation()
        self.beginSelfLayersObservation()
        self.beginSelfLayerObservation()
        self.beginSelfFeaturesObservation()

    def endSelfNotificationObservation(self):
        self.endSelfLayersObservation()
        self.endSelfLayerObservation()
        self.endSelfFeaturesObservation()
        super().endSelfNotificationObservation()
        self._font = None

    # default layer changed (changes cmap)

    def beginSelfLayersObservation(self):
        layers = self.font.layers
        layers.addObserver(
            observer=self,
            methodName="_layerSetDefaultLayerWillChange",
            notification="LayerSet.DefaultLayerWillChange",
        )
        layers.addObserver(
            observer=self,
            methodName="_layerSetDefaultLayerChanged",
            notification="LayerSet.DefaultLayerChanged",
        )

    def endSelfLayersObservation(self):
        layers = self.font.layers
        layers.removeObserver(
            observer=self, notification="LayerSet.DefaultLayerWillChange"
        )
        layers.removeObserver(
            observer=self, notification="LayerSet.DefaultLayerChanged"
        )

    def _layerSetDefaultLayerWillChange(self, notification):
        self.endSelfLayerObservation()

    def _layerSetDefaultLayerChanged(self, notification):
        self.beginLayerObservation()
        self._postNeedsUpdateNotification()

    # cmap change

    def beginSelfLayerObservation(self):
        layer = self.font.layers.defaultLayer
        layer.addObserver(
            observer=self,
            methodName="_layerGlyphNameChanged",
            notification="Layer.GlyphNameChanged",
        )
        layer.addObserver(
            observer=self,
            methodName="_layerGlyphUnicodesChanged",
            notification="Layer.GlyphUnicodesChanged",
        )

    def endSelfLayerObservation(self):
        layer = self.font.layers.defaultLayer
        layer.removeObserver(observer=self, notification="Layer.GlyphNameChanged")
        layer.removeObserver(observer=self, notification="Layer.GlyphUnicodesChanged")

    def _layerGlyphNameChanged(self, notification):
        self._postNeedsUpdateNotification()

    def _layerGlyphUnicodesChanged(self, notification):
        self._postNeedsUpdateNotification()

    # feature text change

    def beginSelfFeaturesObservation(self):
        features = self.font.features
        features.addObserver(
            observer=self,
            methodName="_featuresTextChanged",
            notification="Features.TextChanged",
        )

    def endSelfFeaturesObservation(self):
        features = self.font.features
        features.removeObserver(observer=self, notification="Features.TextChanged")

    def _featuresTextChanged(self, notification):
        self._destroyCachedTables()
        self._postNeedsUpdateNotification()

    # posting

    def _destroyCachedTables(self):
        self.postNotification("LayoutEngine._DestroyCachedTables")

    def _postNeedsUpdateNotification(self):
        self._needsInternalUpdate = True
        self.postNotification(self.changeNotificationName)

    # ----------
    # Engine API
    # ----------

    def process(self, text):
        if not text:
            return []
        if self._needsInternalUpdate:
            self._updateEngine()

        # TODO: reuse buffer?
        buf = hb.Buffer.create()
        if isinstance(text, list):
            font = self.font
            unicodes = []
            for name in text:
                uni = font.unicodeData.unicodeForGlyphName(name)
                if uni is None:
                    # TODO: use a dict instead?
                    gid = self._glyphOrder.index(name)
                    uni = CH_GID_PREFIX + gid
                unicodes.append(uni)
            buf.add_codepoints(unicodes, len(unicodes), 0, len(unicodes))
        else:
            buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self._hbFont, buf, list(self._fontFeatures.values()))

        glyphRecords = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            glyphName = self._glyphOrder[info.codepoint]
            if glyphName not in self.font:
                continue
            record = GlyphRecord()
            record.glyph = self.font[glyphName]
            record.cluster = info.cluster
            record.xOffset = pos.x_offset
            record.yOffset = pos.y_offset
            record.xAdvance = pos.x_advance
            record.yAdvance = pos.y_advance
            glyphRecords.append(record)
        del buf
        return glyphRecords

    def getScriptList(self):
        self._updateEngine()
        # XXX: for now we only list GSUB
        tags = self._hbFont.face.ot_layout.table_get_script_tags(
            hb.tag_from_string("GSUB")
        )
        return [hb.tag_to_string(t) for t in tags]

    def getLanguageList(self):
        self._updateEngine()
        # XXX: for now we only list GSUB, default script
        tags = self._hbFont.face.ot_layout.script_get_language_tags(
            hb.tag_from_string("GSUB"), 0
        )
        return [hb.tag_to_string(t) for t in tags]

    def getFeatureList(self):
        self._updateEngine()
        # XXX: for now we only list GSUB, default script, default language
        tags = self._hbFont.face.ot_layout.language_get_feature_tags(
            hb.tag_from_string("GSUB"), 0, 0xFFFF
        )
        return [hb.tag_to_string(t) for t in tags]

    def getFeatureState(self, name):
        ret = self._fontFeatures.get(name)
        if ret is not None:
            return ret.value
        return ret

    def setFeatureState(self, name, state):
        if state is None:
            if name in self._fontFeatures:
                del self._fontFeatures[name]
            return
        #
        if name in self._fontFeatures:
            feature = self._fontFeatures[name]
        else:
            feature = hb.Feature.from_string(name)
        feature.value = state
        # TODO: start, end
        self._fontFeatures[name] = feature
