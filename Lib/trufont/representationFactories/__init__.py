from defcon import Font, Glyph, Component, registerRepresentationFactory
from trufont.representationFactories.glyphCellFactory import (
    TFGlyphCellFactory)
from trufont.representationFactories.glyphViewFactory import (
    ComponentQPainterPathFactory, FilterSelectionFactory,
    FilterSelectionQPainterPathFactory, SplitLinesQPainterPathFactory)
from trufont.representationFactories.openTypeFactory import (
    TTFontFactory, QuadraticTTFontFactory)

_fontFactories = {
    "TruFont.TTFont": (TTFontFactory, None),
    "TruFont.QuadraticTTFont": (QuadraticTTFontFactory, None),
}
# TODO: fine-tune the destructive notifications
_glyphFactories = {
    "TruFont.SplitLinesQPainterPath": (
        SplitLinesQPainterPathFactory, None),
    "TruFont.FilterSelection": (
        FilterSelectionFactory, ("Glyph.Changed", "Glyph.SelectionChanged")),
    "TruFont.FilterSelectionQPainterPath": (
        FilterSelectionQPainterPathFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged")),
    "TruFont.GlyphCell": (
        TFGlyphCellFactory, None),
}
_componentFactories = {
    "TruFont.QPainterPath": (
        ComponentQPainterPathFactory, (
            "Component.Changed", "Component.BaseGlyphDataChanged")),
}


def registerAllFactories():
    for name, (factory, destructiveNotifications) in _fontFactories.items():
        registerRepresentationFactory(
            Font, name, factory,
            destructiveNotifications=destructiveNotifications)
    for name, (factory, destructiveNotifications) in _glyphFactories.items():
        registerRepresentationFactory(
            Glyph, name, factory,
            destructiveNotifications=destructiveNotifications)
    for name, (factory, destructiveNotifications) in \
            _componentFactories.items():
        registerRepresentationFactory(
            Component, name, factory,
            destructiveNotifications=destructiveNotifications)
