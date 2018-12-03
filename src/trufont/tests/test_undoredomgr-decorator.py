"""  Class and  """
import sys
import logging
import os

import trufont.util.loggingstuff as logstuff
import trufont.objects.undoredomgr as undoredomgr

from tfont.objects import Layer
from tfont.objects import Font

from trufont.objects.truglyph import TruGlyph
from trufont.controls import propertiesView

def expand_param(Layer: Layer, *args, **kwargs):
    return layer, "test_decorator"

class FrameMock(object):
    
    def OnUpdateUndoRedoMenu(self, undoredo: undoredomgr.UndoRedoMgr):
        pass

def test_decorator(logger: logging.Logger = logging.getLogger(logstuff.LOGGER_UNDOREDO)):
    """ Untis Tests for UndoRedoMgr"""
    logger.info("======== Start of test")
    logger.info(sys.version)
    logger.setLevel(logging.DEBUG)
    font = Font()
    fontname = font.familyName
    char = name = "W"
    tglyph = TruGlyph("{}-{}".format(fontname, name), unicodes=["%04X" % ord(char)])
    font.glyphs.append(tglyph)
    tglyph._parent = font
    tglyph.frame = FrameMock()
    tglyph.debug = True
    tglyph.disable_undoredo = False

    logger.info("TEST URM-DECO: tglyph is {}".format(tglyph))
    tglyph.layerForMaster(None)
    # layer = Layer(fontname)
    # layer._parent = font
    # tglyph.layers.append(layer)
    layer = tglyph.layers[0]
    tglyph.load_from_undoredo(layer)
    logger.info("TEST URM-DECO: layer is {}".format(layer))

    seq = 0
    mgr = tglyph.get_undoredo()
    logger.info("TEST URM-DECO: {:02d} -> undo: {} / redo: {}".format(seq, mgr.len_undo(), 
                                mgr.len_redo()))

    seq += 1
    s = layer.snapshot()
    s1 = layer.snapshot()
    assert s == s1
    logger.info("TEST URM-DECO: {:02d} -> undo: {} / redo: {}".format(seq, mgr.len_undo(), 
                                mgr.len_redo()))

    seq += 1
    try:
        for path in layer.paths:
            path.selected = True 
        propertiesView._alignVCenter(layer, tglyph, "None")
    except:
        logger.info("TEST URM-DECO: {:02d} Failed".format(seq))
        assert False
    else:
        logger.info("TEST URM-DECO: {:02d} Successed".format(seq))
        assert True 
    logger.info("TEST URM-DECO: {:02d} -> undo: {} / redo: {}".format(seq, mgr.len_undo(), 
                                mgr.len_redo()))

    seq += 1
    try:
        for path in layer.paths:
            path.selected = True 
        old_func = layer.snapshot
        layer.snaphot = (lambda x: 1/0) 
        propertiesView._alignVcenter(layer, tglyph, "None")
    except:
        logger.info("TEST URM-DECO: {:02d} Failed".format(seq))
        layer.snapshot = old_func
        assert True
    else:
        logger.info("TEST URM-DECO: {:02d} Successed".format(seq))
        assert s != layer.snapshot()
    logger.info("TEST URM-DECO: {:02d} -> undo: {} / redo: {}".format(seq, mgr.len_undo(), 
                                mgr.len_redo()))


if __name__ == "__main__":
    test_decorator(logstuff.create_stream_logger())