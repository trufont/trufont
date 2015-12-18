from defcon import Glyph, Component, Image, registerRepresentationFactory
from defconQt.representationFactories.qPainterPathFactory import (
    QPainterPathFactory)
from defconQt.representationFactories.glyphViewFactory import (
    NoComponentsQPainterPathFactory, OnlyComponentsQPainterPathFactory,
    SplitLinesQPainterPathFactory, ComponentQPainterPathFactory,
    FilterSelectionFactory, FilterSelectionQPainterPathFactory,
    OutlineInformationFactory, QPixmapFactory, StartPointsInformationFactory)

# TODO: add a glyph pixmap factory parametrized on glyph size
# TODO: fine-tune the destructive notifications
_glyphFactories = {
    "defconQt.QPainterPath": (QPainterPathFactory, None),
    "defconQt.OnlyComponentsQPainterPath": (
        OnlyComponentsQPainterPathFactory, None),
    "defconQt.NoComponentsQPainterPath": (
        NoComponentsQPainterPathFactory, None),
    "defconQt.SplitLinesQPainterPath": (
        SplitLinesQPainterPathFactory, None),
    "defconQt.FilterSelection": (
        FilterSelectionFactory, ("Glyph.Changed", "Glyph.SelectionChanged")),
    "defconQt.FilterSelectionQPainterPath": (
        FilterSelectionQPainterPathFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged")),
    "defconQt.OutlineInformation": (
        OutlineInformationFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged")),
    "defconQt.StartPointsInformation": (
        StartPointsInformationFactory, None),
}
_componentFactories = {
    "defconQt.QPainterPath": (
        ComponentQPainterPathFactory, ("Component.Changed",
                                       "Component.BaseGlyphDataChanged")),
}
_imageFactories = {
    "defconQt.QPixmap": (
        QPixmapFactory, ("Image.FileNameChanged", "Image.ColorChanged",
                         "Image.ImageDataChanged"))
}


def registerAllFactories():
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
