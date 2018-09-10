from tfont.objects import Glyph
import trufont
import wx
from wx import GetTranslation as tr


class AddGlyphsDialog(wx.Dialog):

    def __init__(self, parent, font):
        super().__init__(parent)
        self.SetTitle(tr("Add Glyphs…"))

        self._font = font
        self.textCtrl = wx.TextCtrl(self)

        # we could add a contextual help button
        # docs.wxwidgets.org/trunk/classwx_context_help_button.html#details
        btnSizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK, tr("Add"))
        btn.SetDefault()
        btnSizer.AddButton(btn)
        btn_ = wx.Button(self, wx.ID_CANCEL)
        btnSizer.AddButton(btn_)
        btnSizer.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.textCtrl, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btnSizer, 0, wx.ALL, 5)
        self.SetSizer(sizer)
        self.SetSize(wx.Size(400, 160))
        self.Centre()

        self.Bind(wx.EVT_BUTTON, self.OnOK, btn)

    def OnOK(self, event):
        text = self.textCtrl.GetValue()
        names = text.split(' ')
        if not names:
            self.Close()
            return
        glyphs = self._font.glyphs
        existing = set(filter(lambda name: name in glyphs, names))
        if existing:
            text = tr("Some glyphs are already present in the font.")
            caption = " ".join(existing)
            with wx.MessageDialog(
                    self, text,
                    style=wx.YES_NO | wx.CANCEL | wx.ICON_WARNING) as dialog:
                dialog.SetExtendedMessage(caption)
                dialog.SetYesNoLabels(tr("Replace"), tr("Ignore"))
                ret = dialog.ShowModal()
            if ret == wx.ID_YES:
                pass
            elif ret == wx.ID_NO:
                names = list(filter(lambda name: name not in existing, names))
            else:
                return
        # TODO check for names with invalid characters?
        for name in names:
            glyphs.append(Glyph(name))
        if names:
            trufont.TruFont.updateUI()
        self.Close()
