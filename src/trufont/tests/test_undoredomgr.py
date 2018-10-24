"""  Class and  """
import sys
import logging
import os

from typing import Optional, Any, Union, Tuple

import trufont.util.deco4class as deco4class
import trufont.util.loggingstuff as logstuff

import trufont.objects.undoredomgr as undoredomgr

# constants



def test_undoredomgr(logger: logging.Logger = logging.getLogger(logstuff.LOGGER_UNDOREDO)):
    """ Untis Tests for UndoRedoMgr"""
    logger.info("======== Start of test")
    mgr = undoredomgr.UndoRedoMgr("test", logger)
    mgr.set_callback_after_undo(print, "\t"*3, "callback on undo")
    mgr.set_callback_after_redo(print, "\t"*4, "CALLBACK ON REDO")

    seq = 1   
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))

    try: 
        mgr.undo()
    except Exception as e:
        logger.warning("Except - undo on an empty stack")
        assert isinstance(e, IndexError) and mgr.len_undo() == 0

    seq += 1
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))
    logger.info(mgr.str_state())
    mgr.append_action(undoredomgr.Action("A"))
    mgr.append_action(undoredomgr.Action("B", logger.info("test callback undo")))
    assert mgr.len_undo() == 2 and mgr.len_redo() == 0
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))


    seq += 1
    action = mgr.undo()
    assert mgr.len_undo() == 1 and mgr.len_redo() == 1
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))

    seq += 1
    action = mgr.redo()
    assert mgr.len_undo() == 2 and mgr.len_redo() == 0
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))
    
    seq += 1
    action = mgr.undo()
    assert mgr.len_undo() == 1 and mgr.len_redo() == 1
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))

    seq += 1
    mgr.append_action(action)
    mgr.append_action(undoredomgr.Action('C', mgr))
    assert mgr.len_undo() == 3 and mgr.len_redo() == 0
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))

    seq += 1
    action = mgr.undo()
    assert mgr.len_undo() == 2 and mgr.len_redo() == 1
    logger.error("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))
    
    seq += 1
    action = mgr.redo()
    assert mgr.len_undo() == 3 and mgr.len_redo() == 0
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))

    seq += 1
    try:
        action = mgr.redo()
    except Exception as e:
        logger.warning("Except - redo on an empty stack")
        assert isinstance(e, IndexError) and mgr.len_redo() == 0
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))

    seq += 1
    len_undo = mgr.len_undo()
    for _ in range(len_undo):
        action = mgr.undo()
    assert mgr.len_undo() == 0 and mgr.len_redo() == 3
    logger.info("{:02d} -> undo: {} / redo: {}".format(seq, mgr.show_undo(), mgr.show_redo()))
    
    logger.info("----------- End of test")
    
