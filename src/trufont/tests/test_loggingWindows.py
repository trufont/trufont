# file:  test_loggingWindows.py
import sys
import logging

import wx
import trufont.windows.loggingWindows as loggingWindows
import trufont.util.loggingstuff as logstuff

def test_loggingwindows(log: logging.Logger=logstuff.create_stream_logger(logstuff.LOGGER_LOGGING),
                        app: wx.PySimpleApp= wx.PySimpleApp()):
    """ test a window wx with a multiline handler """

    wxLog = loggingWindows.LoggingWindow(None, logger=log, autolog_msg=True)
    log.info(sys.version)
    log.info("levels -> {}".format(loggingWindows.LEVELS))
    log.info("strlevels -> {}".format(loggingWindows.STR_LEVELS))
    log.info("Starting .....")
    wxLog.Show()
    app.MainLoop()
    log.info("This is the end")

if __name__ == "__main__":
    # constants

    app = wx.PySimpleApp()
    #logger = logstuff.create_stream_logger("")
    logger = logstuff.create_timedrotating_logger("")
    test_loggingwindows(logger, app)
