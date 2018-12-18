# file:  wxHandler4log.py

import sys
import os

import wx
import logging
import logging.handlers


# constants
STR_FMT = '%(asctime)s : %(levelname)s : %(filename)20s[%(lineno)03d)] : %(message)s'
DATE_FMT = '%d/%m/%Y %H:%M:%S'

LOGGER_BASE =  __name__ # "trufont"
LOGGER_LOGGING = LOGGER_BASE + ".logging"
LOGGER_UNDOREDO = LOGGER_BASE + ".undoredomgr"
LOGGER_CLASSFUNCS = LOGGER_BASE + ".classfuncs"

def create_default_logger(logger_name: str=LOGGER_BASE, fmt: str=STR_FMT, 
    date_fmt: str=DATE_FMT) -> logging.Logger:
    """ Create a basicconfig  logger """
    logging.basicConfig(format=fmt, datefmt=date_fmt, level=logging.INFO)
    return logging.getLogger()

def create_stream_logger(logger_name: str=LOGGER_BASE, fmt: str=STR_FMT, 
                        date_fmt: str=DATE_FMT) -> logging.Logger:
    """ Create a local logger """
    logger = logging.getLogger(logger_name)
    hdlr = logging.StreamHandler(stream=sys.stdout)
    fmtr = logging.Formatter(fmt, date_fmt)
    hdlr.setFormatter(fmtr)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)

    return logger


def create_timedrotating_logger(logger_name: str=LOGGER_BASE, fmt: str=STR_FMT, 
                                date_fmt: str=DATE_FMT) -> logging.Logger:
    """ Create a TimedRotatingFileHandler on 7 daysfor a main logger """
    logger = logging.getLogger(logger_name)
    where = os.getenv("trufont_logpath")
    # where are create log file
    if not where:
        where = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(where):
            os.mkdir(where)

    hdlr = logging.handlers.TimedRotatingFileHandler(os.path.join(where, 'trufont.log'), 
                                                    'midnight', 1, 7)
    fmtr = logging.Formatter(fmt, date_fmt)
    hdlr.setFormatter(fmtr)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)

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

