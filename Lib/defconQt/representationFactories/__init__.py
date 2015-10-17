from defcon.objects.glyph import addRepresentationFactory
from defconQt.representationFactories.qPainterPathFactory import QPainterPathFactory
from defconQt.representationFactories.glyphViewFactory import NoComponentsQPainterPathFactory, OnlyComponentsQPainterPathFactory, OutlineInformationFactory, StartPointsInformationFactory

_factories = {
    "defconQt.QPainterPath" : QPainterPathFactory,
    "defconQt.OnlyComponentsQPainterPath" : OnlyComponentsQPainterPathFactory,
    "defconQt.NoComponentsQPainterPath" : NoComponentsQPainterPathFactory,
    "defconQt.OutlineInformation" : OutlineInformationFactory,
    "defconQt.StartPointsInformation" : StartPointsInformationFactory,
}

def registerAllFactories():
    for name, factory in _factories.items():
        addRepresentationFactory(name, factory)
