from defconQt.genericSettings import GenericSettings


class DisplayStyleSettings(GenericSettings):
    _presets = (
        ('Default', dict(
            activeLayerOnTop=True, activeLayerFilled=True,
            otherLayersFilled=False, activeLayerUseLayerColor=False,
            otherLayerUseLayerColor=True, drawOtherLayers=True
        )), ('Layer Fonts', dict(
            activeLayerOnTop=False, activeLayerFilled=True,
            otherLayersFilled=True, activeLayerUseLayerColor=True,
            otherLayerUseLayerColor=True, drawOtherLayers=True
        ))
    )

    _items = (
        ('activeLayerOnTop', ('Active Layer on Top', True)),
        ('activeLayerFilled', ('Active Layer Filled', True)),
        ('activeLayerUseLayerColor', ('Active Layer use Custom Color', False)),
        ('otherLayersFilled', ('Other Layers Filled', False)),
        ('otherLayerUseLayerColor', ('Other Layers use Custom Color', True)),
        ('drawOtherLayers', ('Show Other Layers', True))
    )
