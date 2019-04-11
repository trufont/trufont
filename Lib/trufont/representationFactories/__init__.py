from defcon import Component, Glyph, registerRepresentationFactory

from trufont.representationFactories.glyphCellFactory import TFGlyphCellFactory
from trufont.representationFactories.glyphViewFactory import (
    ComponentQPainterPathFactory,
    FilterSelectionFactory,
    SelectedComponentsQPainterPathFactory,
    SelectedContoursQPainterPathFactory,
    SplitLinesQPainterPathFactory,
)

# TODO: fine-tune the destructive notifications
_glyphFactories = {
    "TruFont.SelectedComponentsQPainterPath": (
        SelectedComponentsQPainterPathFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged"),
    ),
    "TruFont.SplitLinesQPainterPath": (SplitLinesQPainterPathFactory, None),
    "TruFont.FilterSelection": (
        FilterSelectionFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged"),
    ),
    "TruFont.SelectedContoursQPainterPath": (
        SelectedContoursQPainterPathFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged"),
    ),
    "TruFont.GlyphCell": (TFGlyphCellFactory, None),
}
_componentFactories = {
    "TruFont.QPainterPath": (
        ComponentQPainterPathFactory,
        ("Component.Changed", "Component.BaseGlyphDataChanged"),
    )
}


def registerAllFactories():
    for name, (factory, destructiveNotifications) in _glyphFactories.items():
        registerRepresentationFactory(
            Glyph, name, factory, destructiveNotifications=destructiveNotifications
        )
    for name, (factory, destructiveNotifications) in _componentFactories.items():
        registerRepresentationFactory(
            Component, name, factory, destructiveNotifications=destructiveNotifications
        )
