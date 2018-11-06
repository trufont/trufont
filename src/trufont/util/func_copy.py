from tfont.objects import Path, Point, Layer

from tfont.converters.tfontConverter import TFontConverter
TFONT_CONV = TFontConverter(indent=None)
TFONT_CONVU = TFontConverter()
from typing import List
import logging
import copy

def copypathsfromlayer(layer: Layer) -> List[Path]:
    """ manual deep copy of paths of layer """
    lpaths = []
    for path in layer._paths:
        new_path = Path()
        # copy bounds
        new_path._bounds = copy.copy(path._bounds)

        # copy points
        new_path._points = [copy.copy(pt) for pt in path._points]

        # parents etc ...
        new_path._parent = path._parent 
        new_path._id = path._id
        new_path._graphicsPath = path._graphicsPath

        # keep it
        lpaths.append(new_path)

    return lpaths


def undoredo_copypathsfromlayer(layer: Layer, old_paths: Path, old_operation:str):
    """ restore data paths from an undo or redo actions """
    #set old values
    layer.paths[:] = old_paths
    layer.paths.applyChange()


def copylayerfromlayer(layer: Layer) -> "blabla":
    """ copy full layer """ 
    save = TFONT_CONV.unstructure(layer)
    logging.debug("COPYLAYER: copylayer -> {}".format(save))
    return save 


def undoredo_copylayerfromlayer(layer: Layer, old_layer: "blabla", operation:str):
    """ restore layer from an undo or redo actions """
    logging.info("COPYLAYER: layer is {}".format(layer))
    logging.info("COPYLAYER: operation is {}".format(operation))
    logging.info("COPYLAYER: old_layer is {}".format(old_layer))

    try:
        logging.info("COPYLAYER: before structure")        
        val = TFONT_CONVU.structure(old_layer, Layer.__class__)
        logging.info("COPYLAYER: val is {}".format(type(val)))
        layer = val
        logging.info("COPYLAYER: new layer is {}".format(val))


    # tglyph = layer._parent
    # for lay in tglyph:
    #     if lay._name == old_layer._name

    except Exception as e:
        logging.error("COPYLAYER: error on ".format(str(e)))



def _copylayerfromlayer(layer: Layer) -> Layer:
    """ copy full layer """ 
    logging.debug("COPYLAYER: copylayer")
    try:
        save = layer.copy()
        if save:
            save._name = layer._name
            save.masterName = layer.masterName
            logging.debug("COPYLAYER: copylayer -> {} anchors: {}, guidelines: {}".format(save, save._anchors, save._guidelines)) 
    except Exception as e:
        logging.error("COPYLAYER: copylayerfromlayer error {}".format(str(e)))

    return save


def _undoredo_copylayerfromlayer(layer: Layer, old_layer: Layer, old_operation:str):
    """ restore layer from an undo or redo actions """
    logging.debug("COPYLAYER: actual Layer -> {} , old Layer -> {}".format(id(layer), id(old_layer)))
    logging.debug("COPYLAYER: actual Layer -> {} anchors: {}, guidelines: {}".format(layer, layer._anchors, layer._guidelines)) 
    logging.debug("COPYLAYER: old Layer -> {} anchors: {}, guidelines: {}".format(old_layer, old_layer._anchors, old_layer._guidelines)) 
    layer = old_layer
    logging.debug("COPYLAYER: after copy -> {} anchors: {}, guidelines: {}".format(layer, layer._anchors, layer._guidelines)) 

# LAYER_EXCLUDED_ATTRIBS = 
LAYER_ATTRIBS = set(Layer.__slots__)\
                - {'masterName', '_name','_closedGraphicsPath', '_openGraphicsPath', '_parent', '__weakref__'} 
def undoredo_copylayerfromlayer_old(layer: Layer, old_layer: Layer, old_operation:str):
    """ restore layer from an undo or redo actions """
    logging.debug("COPYLAYER: Layer dict: {}".format(LAYER_ATTRIBS))
    logging.debug("COPYLAYER: actual Layer -> {} anchors: {}, guidelines: {}".format(layer, layer._anchors, layer._guidelines)) 
    logging.debug("COPYLAYER: actual Layer -> {} anchors: {}, guidelines: {}".format(old_layer, old_layer._anchors, old_layer._guidelines)) 

    # layer = copy(old_layer)
    for attr in LAYER_ATTRIBS:
        logging.debug("COPYLAYER: {} = {}".format(attr, getattr(old_layer, attr)))
        old_value = getattr(old_layer, attr)
        if old_value:
            old_value = copypathsfromlayer(old_layer)  if attr == '_path' else copy(old_value)
        setattr(layer, attr, old_value) 
