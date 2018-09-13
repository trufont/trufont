import keyword
from tfont import objects
import traceback
import trufont
from trufont.objects import icons
import wx
from wx import GetTranslation as tr, stc

ENABLE_FOLD = False

objects_dict = vars(objects)
for key in list(objects_dict.keys()):
    if key.startswith("__"):
        del objects_dict[key]


class ScriptingWindow(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetIcon(icons.GetUserIcon("app.png", 32, 32, self))
        self.SetTitle(tr("Scripting – %s") % wx.GetApp().GetAppDisplayName())

        self.editor = editor = stc.StyledTextCtrl(self)

        editor.SetMarginType(0, stc.STC_MARGIN_NUMBER)
        editor.SetMarginWidth(0, 30)
        if ENABLE_FOLD:
            editor.SetMarginWidth(2, 14)
            editor.SetMarginMask(2, stc.STC_MASK_FOLDERS)
            editor.SetFoldMarginColour(True, "white")
            editor.SetFoldMarginHiColour(True, wx.Colour(233, 233, 233))

        editor.SetLexer(stc.STC_LEX_PYTHON)
        # further subdivide that list
        # https://bitbucket.org/birkenfeld/pygments-main/src/7941677dc77d4f2bf0bbd6140ade85a9454b8b80/pygments/lexers/python.py?at=default&fileviewer=file-view-default#python.py-51
        # and add keywords for TruFont, etc. also tfont types?
        editor.SetKeyWords(0, " ".join(keyword.kwlist))

        baseColor = wx.Colour(35, 36, 38)
        editor.StyleSetFaceName(stc.STC_STYLE_DEFAULT, "Consolas")
        editor.StyleSetForeground(stc.STC_STYLE_DEFAULT, baseColor)
        editor.StyleSetSize(stc.STC_STYLE_DEFAULT, 11)

        editor.StyleSetForeground(stc.STC_STYLE_LINENUMBER, "Grey")
        editor.StyleSetBackground(stc.STC_STYLE_LINENUMBER, wx.Colour(228, 228, 228))

        # Comments
        editor.StyleSetForeground(stc.STC_P_COMMENTLINE, wx.Colour(104, 104, 104))
        # Number
        editor.StyleSetForeground(stc.STC_P_NUMBER, wx.Colour(227, 98, 9))
        # String
        strColor = wx.Colour(255, 27, 147)
        editor.StyleSetForeground(stc.STC_P_CHARACTER, strColor)
        editor.StyleSetForeground(stc.STC_P_COMMENTBLOCK, strColor)
        editor.StyleSetForeground(stc.STC_P_STRING, strColor)
        editor.StyleSetForeground(stc.STC_P_TRIPLE, strColor)
        editor.StyleSetForeground(stc.STC_P_TRIPLEDOUBLE, strColor)
        # Keyword
        editor.StyleSetForeground(stc.STC_P_WORD, wx.Colour(45, 95, 235))
        # Identifier
        # wx.Colour(120, 91, 160))
        editor.StyleSetForeground(stc.STC_P_CLASSNAME, wx.Colour(96, 106, 161))
        editor.StyleSetForeground(stc.STC_P_DEFNAME, wx.Colour(96, 106, 161))
        # Misc
        # stc.STC_P_DECORATOR
        # stc.STC_P_OPERATOR

        if ENABLE_FOLD:
            editor.SetProperty("fold", "1")
            fgColor = wx.Colour(243, 243, 243)
            editor.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_BOXMINUS, fgColor, "Grey"
            )
            editor.MarkerDefine(
                stc.STC_MARKNUM_FOLDER, stc.STC_MARK_BOXPLUS, fgColor, "Grey"
            )
            editor.MarkerDefine(
                stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_VLINE, fgColor, "Grey"
            )
            editor.MarkerDefine(
                stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_LCORNER, fgColor, "Grey"
            )
            editor.MarkerDefine(
                stc.STC_MARKNUM_FOLDEREND,
                stc.STC_MARK_BOXPLUSCONNECTED,
                fgColor,
                "Grey",
            )
            editor.MarkerDefine(
                stc.STC_MARKNUM_FOLDEROPENMID,
                stc.STC_MARK_BOXMINUSCONNECTED,
                fgColor,
                "Grey",
            )
            editor.MarkerDefine(
                stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER, fgColor, "Grey"
            )
            editor.MarkerEnableHighlight(stc.STC_MARKNUM_FOLDEROPEN)

        editor.IndicatorSetStyle(1, stc.STC_INDIC_HIDDEN)
        editor.SetScrollWidth(1)
        editor.SetScrollWidthTracking(True)

        runButton = wx.Button(self, wx.ID_ANY, "&Run")
        self.Bind(wx.EVT_BUTTON, self.OnButton, runButton)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(editor, 1, wx.EXPAND)
        sizer.Add(runButton, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetSize((600, 800))
        self.Centre()

    def runScript(self):
        script = self.editor.GetText()
        global_vars = {"__builtins__": __builtins__, "TruFont": trufont.TruFont}
        global_vars.update(objects_dict)
        try:
            code = compile(script, "<string>", "exec")
            exec(code, global_vars)
        except:
            traceback.print_exc()
        trufont.TruFont.updateUI()

    def OnButton(self, event):
        self.runScript()
