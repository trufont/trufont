from defcon import Font, Glyph, Component, Image, registerRepresentationFactory
from trufont.representationFactories.qPainterPathFactory import (
    QPainterPathFactory)
from trufont.representationFactories.glyphViewFactory import (
    NoComponentsQPainterPathFactory, OnlyComponentsQPainterPathFactory,
    SplitLinesQPainterPathFactory, ComponentQPainterPathFactory,
    FilterSelectionFactory, FilterSelectionQPainterPathFactory,
    OutlineInformationFactory, QPixmapFactory)
from trufont.representationFactories.openTypeFactory import (
    TTFontFactory, QuadraticTTFontFactory)

_fontFactories = {
    "trufont.TTFont": (TTFontFactory, None),
    "trufont.QuadraticTTFont": (QuadraticTTFontFactory, None),
}
# TODO: add a glyph pixmap factory parametrized on glyph size
# TODO: fine-tune the destructive notifications
_glyphFactories = {
    "trufont.QPainterPath": (QPainterPathFactory, None),
    "trufont.OnlyComponentsQPainterPath": (
        OnlyComponentsQPainterPathFactory, None),
    "trufont.NoComponentsQPainterPath": (
        NoComponentsQPainterPathFactory, None),
    "trufont.SplitLinesQPainterPath": (
        SplitLinesQPainterPathFactory, None),
    "trufont.FilterSelection": (
        FilterSelectionFactory, ("Glyph.Changed", "Glyph.SelectionChanged")),
    "trufont.FilterSelectionQPainterPath": (
        FilterSelectionQPainterPathFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged")),
    "trufont.OutlineInformation": (
        OutlineInformationFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged")),
}
_componentFactories = {
    "trufont.QPainterPath": (
        ComponentQPainterPathFactory, ("Component.Changed",
                                       "Component.BaseGlyphDataChanged")),
}
_imageFactories = {
    "trufont.QPixmap": (
        QPixmapFactory, ("Image.FileNameChanged", "Image.ColorChanged",
                         "Image.ImageDataChanged"))
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
    for name, (factory, destructiveNotifications) in _imageFactories.items():
        registerRepresentationFactory(
            Image, name, factory,
            destructiveNotifications=destructiveNotifications)
