"""  Class and  """
import sys
import logging
import os

import trufont.util.loggingstuff as logstuff
import trufont.objects.undoredomgr as undoredomgr

# constants



def test_action(logger: logging.Logger = logging.getLogger(logstuff.LOGGER_UNDOREDO)):
    """ Untis Tests for UndoRedoMgr"""
    logger.info("======== Start of test")

    op = "test"
    undo=1
    redo=2
    args=('tt', True)
    a = undoredomgr.Action(op, undo, redo, args)
    logger.info("1-Action is {}".format(a))

    a = undoredomgr.Action(op, undo, redo, *args)
    logger.info("2-Action is {}".format(a))

    all = undo, redo, args 
    b = undoredomgr.Action(op, *all)
    logger.info("3-Action is {}".format(b))
	
    all = undo, redo, args 
    b = undoredomgr.Action(op, *all).datas_only()
    logger.info("4-Action, datas are {}".format(b))
	


if __name__ == "__main__":
    test_action(logstuff.create_stream_logger())