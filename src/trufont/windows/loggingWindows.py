# file:  wxHandler4log.py
import logging
import random
import wx

import trufont.util.deco4class as deco4class
import trufont.util.loggingstuff as logstuff

#do not keep logging.NOTSET
LEVELS = tuple(value for value in logging._levelToName if value != logging.NOTSET)
STR_LEVELS = tuple(logging._levelToName[value] for value in LEVELS)
START_LEVEL = LEVELS.index(logging.DEBUG)   

def start_logging():
    """ open the logging Windows """
    pass


@deco4class.decorator_classfunc()
class LoggingWindow(wx.Frame):

    def __init__(self, parent, logger: logging.Logger, fmt: str=logstuff.STR_FMT, 
                date_fmt: str=logstuff.DATE_FMT, autolog_msg: bool=False):
        """ init of log frame"""
        self._logger = logger
        self._parent = parent 
        logger.debug("LOGGING: In __init__")

        # build the window        
        TITLE = "Logging To ListBox"
        wx.Frame.__init__(self, parent, wx.ID_ANY, TITLE)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # control in the window
        panel = wx.Panel(self, wx.ID_ANY)
        # TO DO: Multi Column List 
        # ----------------------------
        self.ctrl_log = wx.TextCtrl(panel, wx.ID_ANY, size=(600,200),
                          style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        
        if autolog_msg:
            ctrl_btn = wx.Button(panel, wx.ID_ANY, 'Log something!')
            self.Bind(wx.EVT_BUTTON, self.on_button, ctrl_btn)

        ctrl_reset = wx.Button(panel, wx.ID_ANY, 'Reset List')
        self.Bind(wx.EVT_BUTTON, self.on_reset_list, ctrl_reset)
        
        text_level = wx.StaticText(panel, wx.ID_ANY, "level trace")
        self.ctrl_level = wx.ComboBox(panel, value=STR_LEVELS[START_LEVEL], 
                                    choices = STR_LEVELS, 
                                    style = wx.CB_DROPDOWN | wx.CB_READONLY)
        self.Bind(wx.EVT_TEXT, self.on_combo_text_changed, self.ctrl_level)

        # box to place ctrl 
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl_log, 1, wx.ALL|wx.EXPAND, 10)
        
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(text_level, 0, wx.ALL|wx.RIGHT, 10)
        btnSizer.Add(self.ctrl_level, 0, wx.ALL|wx.RIGHT, 10)
        btnSizer.Add(ctrl_reset, 0, wx.ALL|wx.RIGHT,10)
        if autolog_msg:
            btnSizer.Add(ctrl_btn, 0, wx.ALL|wx.RIGHT, 10)
        sizer.Add(btnSizer)
        panel.SetSizer(sizer)
        
        # add an handler to the current logger
        self.handler = logstuff.WxTextCtrlHandler(self.ctrl_log)
        self.handler.setFormatter(logging.Formatter(fmt, date_fmt))
        self.handler.setLevel(logging.DEBUG)
        self._logger.addHandler(self.handler)

        # size windows
        if self._parent:
            self._logger.debug("LOGGING: Resize windows")
            size = parent.GetSize()
            self.SetSize((size[0], size[1]//3))

    def OnClose(self, event):
        """ close this windows """
        if self._parent:
            self._logger.debug("LOGGING: Close windows")
            self._parent.OnloggingClosed()
        self.Destroy() 

    def on_button(self, event: wx.  Event):
        self._logger.log(random.choice(LEVELS), "LOGGING: More messages ?")


    def on_reset_list(self, event: wx.Event):
        self._logger.info("LOGGING: Reset list ok")
        self.ctrl_log.Clear()

        
    def on_combo_text_changed(self, event: wx.Event):
        """ when changed get position of text from combo list"""
        try:
            pos = self.ctrl_level.GetSelection()
            
            self._logger.info("LOGGING: Level changed to '{}'".format(STR_LEVELS[pos]))
            self.handler.setLevel(LEVELS[pos])
                
        except Exception as e:
            self._logger.error("LOGGING: Error as {}".format(e))

