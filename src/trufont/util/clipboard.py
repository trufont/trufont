import rapidjson as json
from tfont.converters import TFontConverter
from tfont.objects import Anchor, Component, Guideline, Layer, Path
import wx
from typing import List

# we need to serialize the selected attribute


def retrieve(layer: Layer) -> bool:
    data = wx.TextDataObject()
    clipboard = wx.Clipboard.Get()
    if clipboard.Open():
        ok = clipboard.GetData(data)
        clipboard.Close()
        if not ok:
            return False
    try:
        data = json.loads(data.GetText())
    except ValueError:
        # invalid json
        return False
    conv = TFontConverter()
    anchors = data.get("anchors")
    if anchors:
        layer.anchors.update(
            {a.name: a for a in conv.structure(anchors, List[Anchor])}
        )
    components = data.get("components")
    if components:
        layer.components.extend(
            conv.structure(components, List[Component])
        )
    guidelines = data.get("guidelines")
    if guidelines:
        layer.guidelines.extend(
            conv.structure(guidelines, List[Guideline])
        )
    paths = data.get("paths")
    if paths:
        layer.paths.extend(
            conv.structure(paths, List[Path])
        )
    return bool(anchors or components or guidelines or paths)


# add a selectionOnly argument
def store(layer: Layer) -> bool:
    conv = TFontConverter()
    data = {}
    content = []
    for anchor in layer._anchors.values():
        if anchor.selected:
            content.append(anchor)
    if content:
        data["anchors"] = conv.unstructure(content)
        content = []
    for component in layer._components:
        if component.selected:
            content.append(component)
    if content:
        data["components"] = conv.unstructure(content)
        content = []
    master = layer.master
    if master is not None:
        guidelines = layer._guidelines + master._guidelines
    else:
        guidelines = layer._guidelines
    for guideline in guidelines:
        if guideline.selected:
            content.append(guideline)
    if content:
        data["guidelines"] = conv.unstructure(content)
        content = []
    paths = layer.selectedPaths
    if paths:
        data["paths"] = conv.unstructure(paths)
    if data:
        clipboard = wx.Clipboard.Get()
        if clipboard.Open():
            clipboard.SetData(wx.TextDataObject(json.dumps(data)))
            clipboard.Close()
            return True
    return False
