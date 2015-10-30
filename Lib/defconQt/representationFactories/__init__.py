from defcon import Glyph, registerRepresentationFactory
from defconQt.representationFactories.qPainterPathFactory import (
    QPainterPathFactory)
from defconQt.representationFactories.glyphViewFactory import (
    NoComponentsQPainterPathFactory, OnlyComponentsQPainterPathFactory,
    OutlineInformationFactory, StartPointsInformationFactory)

# TODO: add a glyph pixmap factory parametrized on glyph size
# TODO: fine-tune the destructive notifications
_factories = {
    "defconQt.QPainterPath": (QPainterPathFactory, None),
    "defconQt.OnlyComponentsQPainterPath": (
        OnlyComponentsQPainterPathFactory, None),
    "defconQt.NoComponentsQPainterPath": (
        NoComponentsQPainterPathFactory, None),
    "defconQt.OutlineInformation": (
        OutlineInformationFactory, None),
    "defconQt.StartPointsInformation": (
        StartPointsInformationFactory, None),
}


def registerAllFactories():
    for name, (factory, destructiveNotifications) in _factories.items():
        registerRepresentationFactory(
            Glyph, name, factory,
            destructiveNotifications=destructiveNotifications)
