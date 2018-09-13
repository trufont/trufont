import wx

NumberModifiedEvent, EVT_NUMBER_MODIFIED = wx.lib.newevent.NewEvent()


class SpinCtrl(wx.TextCtrl):
    # also mouse vertical incr as in Adobe XD
    # and wrapping of values e.g. for rotation 0->360
    # float v. integer spin ctrl
    NUMBER_MODIFIED = EVT_NUMBER_MODIFIED

    def __init__(self, *args, **kwargs):
        kwargs["style"] = kwargs.get("style", 0) | wx.TE_PROCESS_ENTER
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnter)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)

        self._number = 0
        self._suffix = ""
        self.updateValue()

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, value):
        self._number = value
        self.updateValue()

    @property
    def suffix(self):
        return self._suffix

    @suffix.setter
    def suffix(self, value: str):
        self._suffix = value
        self.updateValue()

    def updateValue(self):
        if self.HasFocus():
            self.SetValue(str(self._number))
            self.SelectAll()
        else:
            self.SetValue(f"{self._number}{self._suffix}")

    # ----------
    # wx methods
    # ----------

    def OnEnter(self, event):
        self.Navigate(0)

    def OnKeyDown(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_UP:
            delta = 1
        elif key == wx.WXK_DOWN:
            delta = -1
        else:
            event.Skip()
            return
        if event.ShiftDown():
            delta *= 10
            if event.ControlDown():
                delta *= 10
        self._number += delta
        wx.PostEvent(self, NumberModifiedEvent(number=self._number))
        self.updateValue()

    def OnKillFocus(self, event):
        value = self.GetValue()
        try:
            number = int(value)
        except ValueError:
            try:
                number = float(value)
            except ValueError:
                number = None
        if number is not None:
            self._number = number
            wx.PostEvent(self, NumberModifiedEvent(number=number))
        self.updateValue()
        event.Skip()
        self.Unbind(wx.EVT_KEY_DOWN, self)

    def OnSetFocus(self, event):
        self.SetValue(str(self._number))
        event.Skip()
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        wx.CallAfter(self.SelectAll)
