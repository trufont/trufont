# file:  wxHandler4log.py

import sys
import os

import wx
import logging

# constants
STR_FMT = '%(asctime)s : %(levelname)s : %(filename)20s[%(lineno)03d)] : %(message)s'
DATE_FMT = '%d/%m/%Y %H:%M:%S'

_LOGGER_BASE = "trufont"
LOGGER_LOGGING = _LOGGER_BASE + ".logging"
LOGGER_UNDOREDO = _LOGGER_BASE + ".undoredomgr"
LOGGER_CLASSFUNCS = _LOGGER_BASE + ".classfuncs"


def create_stream_logger(logger_name: str, fmt: str=STR_FMT, 
                        date_fmt: str=DATE_FMT) -> logging.Logger:
    """ Create an local logger """
    logger = logging.getLogger(logger_name)
    hdlr = logging.StreamHandler(stream=sys.stdout)
    fmtr = logging.Formatter(fmt, date_fmt)
    hdlr.setFormatter(fmtr)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)

    return logger


class WxTextCtrlHandler(logging.Handler):
    """ wxControl handler to receive message 
    from logger """ 
    
    def __init__(self, ctrl: wx.TextCtrl):
        """ set the ctrl """
        logging.Handler.__init__(self)
        self.ctrl = ctrl
        

    def emit(self, record: logging.LogRecord):
        """ send the formatting message """
        s = self.format(record) + os.linesep
        wx.CallAfter(self.ctrl.WriteText, s)

