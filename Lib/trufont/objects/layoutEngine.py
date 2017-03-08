from defcon.objects.base import BaseObject
from defconQt.controls.glyphContextView import GlyphRecord
from io import BytesIO
import array
import weakref

try:
    from harfbuzz import HARFBUZZ as HB
    import harfbuzz as hb
except ImportError:
    pass

# TODO: add more parameters
# TODO: make sure we subscribe to appropriate notifications
# TODO: how to shape and have unencoded glyphs input?
# TODO: remove steps from font compilation?


class LayoutEngine(BaseObject):
    changeNotificationName = "LayoutEngine.Changed"

    def __init__(self, font):
        self._needsInternalUpdate = True
        self._font = weakref.ref(font)
        self._GIDToGlyphNameMapping = []
        self._hbFont = None
        super().__init__()
        self.beginSelfNotificationObservation()

    def _get_font(self):
        if self._font is not None:
            return self._font()
        return None

    font = property(_get_font)

    def _get_engine(self):
        if self._needsInternalUpdate:
            self._updateEngine()
        return self._layoutEngine

    engine = property(_get_engine)

    # --------------
    # Engine Updates
    # --------------

    def _updateEngine(self):
        if not self._needsInternalUpdate:
            return
        font = self.font
        otf = font.getRepresentation("TruFont.TTFont")
        self._GIDToGlyphNameMapping = otf.getGlyphOrder()
        a = array.array('B')
        with BytesIO() as f:
            otf.save(f)
            size = f.tell()
            f.seek(0)
            a.fromfile(f, size)

        blob = hb.Blob.create_for_array(a, HB.MEMORY_MODE_READONLY)
        face = hb.Face.create(blob, 0)
        del blob
        font = hb.Font.create(face)
        upem = face.upem
        del face
        font.scale = (upem, upem)
        font.ot_set_funcs()
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
            observer=self, methodName="_layerSetDefaultLayerWillChange",
            notification="LayerSet.DefaultLayerWillChange")
        layers.addObserver(
            observer=self, methodName="_layerSetDefaultLayerChanged",
            notification="LayerSet.DefaultLayerChanged")

    def endSelfLayersObservation(self):
        layers = self.font.layers
        layers.removeObserver(
            observer=self, notification="LayerSet.DefaultLayerWillChange")
        layers.removeObserver(
            observer=self, notification="LayerSet.DefaultLayerChanged")

    def _layerSetDefaultLayerWillChange(self, notification):
        self.endSelfLayerObservation()

    def _layerSetDefaultLayerChanged(self, notification):
        self.beginLayerObservation()
        self._postNeedsUpdateNotification()

    # cmap change

    def beginSelfLayerObservation(self):
        layer = self.font.layers.defaultLayer
        layer.addObserver(
            observer=self, methodName="_layerGlyphUnicodesChanged",
            notification="Layer.GlyphUnicodesChanged")

    def endSelfLayerObservation(self):
        layer = self.font.layers.defaultLayer
        layer.removeObserver(
            observer=self, notification="Layer.GlyphUnicodesChanged")

    def _layerGlyphUnicodesChanged(self):
        self._postNeedsUpdateNotification()

    # feature text change

    def beginSelfFeaturesObservation(self):
        features = self.font.features
        features.addObserver(
            observer=self, methodName="_featuresTextChanged",
            notification="Features.TextChanged")

    def endSelfFeaturesObservation(self):
        features = self.font.features
        features.removeObserver(
            observer=self, notification="Features.TextChanged")

    def _featuresTextChanged(self, notification):
        self._postNeedsUpdateNotification()

    # posting

    def _postNeedsUpdateNotification(self):
        self._needsInternalUpdate = True
        self.postNotification(self.changeNotificationName)

    # ----------
    # Engine API
    # ----------

    def process(self, text):
        self._updateEngine()

        # TODO: reuse buffer?
        buf = hb.Buffer.create()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self._hbFont, buf)

        glyphRecords = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            record = GlyphRecord()
            glyphName = self._GIDToGlyphNameMapping[info.codepoint]
            record.glyph = self.font[glyphName]
            record.index = info.cluster
            record.xOffset = pos.x_offset
            record.yOffset = pos.y_offset
            record.xAdvance = pos.x_advance
            record.yAdvance = pos.y_advance
            glyphRecords.append(record)
        del buf
        return glyphRecords
