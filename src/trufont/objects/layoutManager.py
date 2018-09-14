class LayoutManager:
    __slots__ = "_canvas", "_buffer", "_caretIndex", "_layers"

    def __init__(self, canvas):
        self._canvas = canvas

        self._buffer = None
        self._caretIndex = None
        self._layers = None

        self.updateFeatures()

    @property
    def activeIndex(self):
        # we could also cache this property
        idx = self.caretIndex
        # in rtl mode we "look the other side" of the cursor
        # to get the current layer
        if self._canvas._direction == "rtl":
            idx += 1
            hi = len(self.layers) - 1
            if idx > hi:
                idx = hi
        else:
            if idx < 0:
                idx = 0
        return idx

    @property
    def activeLayer(self):
        layers = self.layers
        if layers:
            return layers[self.activeIndex]
        return None

    @property
    def buffer(self):
        buffer = self._buffer
        if buffer is None:
            canvas = self._canvas
            engine = canvas._font.layoutEngine
            # we ought to disable feat kerning as well when clicking the button
            features = canvas._features
            features["kern"] = canvas._applyKerning
            buffer = self._buffer = engine.process(
                canvas._textBuffer, direction=canvas._direction, features=features
            )
            del features["kern"]
        return buffer

    @property
    def layers(self):
        layers = self._layers
        if layers is None:
            canvas = self._canvas
            layers = []
            glyphs = canvas._font._glyphs
            overrides = canvas._layerOverrides
            for idx, info in enumerate(self.buffer.glyph_infos):
                ol = overrides.get(idx)
                layers.append(
                    ol
                    if ol is not None
                    else glyphs[info.codepoint].layerForMaster(None)
                )
            self._layers = layers
        return layers

    @property
    def caretIndex(self):
        caretIndex = self._caretIndex
        if caretIndex is None:
            canvas = self._canvas
            textPos = canvas._textCursor.position - 1
            caretIndex = -1
            layers = self.layers
            if layers:
                infos = self.buffer.glyph_infos
                rev = canvas._direction == "rtl"
                if rev:
                    infos = reversed(infos)
                size = len(layers)
                for info in infos:
                    if info.cluster > textPos:
                        break
                    if caretIndex >= size:
                        break
                    caretIndex += 1
                if rev:
                    # we looked at the infos in reverse,
                    # now mirror our result (in range -1->size-1
                    # hence the -2)
                    caretIndex = size - caretIndex - 2
            self._caretIndex = caretIndex
        return caretIndex

    @property
    def caretPosition(self):
        caretIndex = self.caretIndex
        x = 0
        if caretIndex >= 0:
            for idx, pos in enumerate(self.buffer.glyph_positions):
                x += pos.x_advance
                if idx == caretIndex:
                    return x
        return x

    @property
    def records(self):
        # TODO: apply kerning
        for idx, (layer, pos) in enumerate(
            zip(self.layers, self.buffer.glyph_positions)
        ):
            yield idx, layer, pos.x_offset, pos.y_offset, pos.x_advance, pos.y_advance

    def clear(self):
        self._buffer = self._caretIndex = self._layers = None

    def clearPosition(self):
        self._caretIndex = None

    def indexAt(self, xPos, lOffset=False):
        buffer = self.buffer
        left = 0
        for idx, pos in enumerate(buffer.glyph_positions):
            x = left + pos.x_offset
            w = pos.x_advance
            if x <= xPos < x + w:
                infos = buffer.glyph_infos
                if lOffset and xPos - w // 2 < x:
                    return infos[idx].cluster
                if self._canvas._direction == "rtl":
                    if not idx:
                        return infos[idx].cluster + 1
                    return infos[idx - 1].cluster
                else:
                    try:
                        return infos[idx + 1].cluster
                    except IndexError:
                        return infos[idx].cluster + 1
            left += w

    def updateFeatures(self):
        canvas = self._canvas
        features = canvas._features
        fontFeatures = canvas._font.layoutEngine.features
        for feat in list(features.keys()):
            try:
                fontFeatures.remove(feat)
            except ValueError:
                del features[feat]
        for feat in fontFeatures:
            features[feat] = False
