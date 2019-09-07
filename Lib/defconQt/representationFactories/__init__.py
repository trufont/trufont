from defcon import Glyph, Image, registerRepresentationFactory

from defconQt.representationFactories.glyphCellFactory import GlyphCellFactory
from defconQt.representationFactories.glyphViewFactory import (
    NoComponentsQPainterPathFactory,
    OnlyComponentsQPainterPathFactory,
    OutlineInformationFactory,
    QPixmapFactory,
)
from defconQt.representationFactories.qPainterPathFactory import QPainterPathFactory

# TODO: fine-tune the destructive notifications
_glyphFactories = {
    "defconQt.QPainterPath": (QPainterPathFactory, None),
    "defconQt.NoComponentsQPainterPath": (NoComponentsQPainterPathFactory, None),
    "defconQt.OnlyComponentsQPainterPath": (OnlyComponentsQPainterPathFactory, None),
    "defconQt.GlyphCell": (GlyphCellFactory, None),
    "defconQt.OutlineInformation": (
        OutlineInformationFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged"),
    ),
}
_imageFactories = {
    "defconQt.QPixmap": (
        QPixmapFactory,
        ("Image.FileNameChanged", "Image.ColorChanged", "Image.ImageDataChanged"),
    )
}


def registerAllFactories():
    for name, (factory, destructiveNotifications) in _glyphFactories.items():
        registerRepresentationFactory(
            Glyph, name, factory, destructiveNotifications=destructiveNotifications
        )
    for name, (factory, destructiveNotifications) in _imageFactories.items():
        registerRepresentationFactory(
            Image, name, factory, destructiveNotifications=destructiveNotifications
        )
