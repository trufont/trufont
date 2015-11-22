from defcon import Glyph, Image, registerRepresentationFactory
from defconQt.representationFactories.qPainterPathFactory import (
    QPainterPathFactory)
from defconQt.representationFactories.glyphViewFactory import (
    NoComponentsQPainterPathFactory, OnlyComponentsQPainterPathFactory,
    SplitLinesQPainterPathFactory,
    OutlineInformationFactory, OutlineInformationFactory_,
    QPixmapFactory, StartPointsInformationFactory)

# TODO: add a glyph pixmap factory parametrized on glyph size
# TODO: fine-tune the destructive notifications
_glyphFactories = {
    "defconQt.QPainterPath": (QPainterPathFactory, None),
    "defconQt.OnlyComponentsQPainterPath": (
        OnlyComponentsQPainterPathFactory, None),
    "defconQt.NoComponentsQPainterPath": (
        NoComponentsQPainterPathFactory, None),
    "defconQt.SplitLinesQPainterPathFactory": (
        SplitLinesQPainterPathFactory, None),
    "defconQt.OutlineInformation": (
        OutlineInformationFactory, None),
    "defconQt.OutlineInformation_": (
        OutlineInformationFactory_, None),
    "defconQt.StartPointsInformation": (
        StartPointsInformationFactory, None),
}
_imageFactories = {
    "defconQt.QPixmap": (
        QPixmapFactory, ["Image.FileNameChanged", "Image.ColorChanged",
                         "Image.ImageDataChanged"])
}


def registerAllFactories():
    for name, (factory, destructiveNotifications) in _glyphFactories.items():
        registerRepresentationFactory(
            Glyph, name, factory,
            destructiveNotifications=destructiveNotifications)
    for name, (factory, destructiveNotifications) in _imageFactories.items():
        registerRepresentationFactory(
            Image, name, factory,
            destructiveNotifications=destructiveNotifications)
