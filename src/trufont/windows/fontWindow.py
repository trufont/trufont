from functools import partial
import os
import string
import subprocess
import trufont
from trufont import __file__ as modulePath, __version__
from trufont.controls import (
    GlyphCanvasView,
    GlyphCellView,
    FontStatusBar,
    GlyphStatusBar,
    FontTabBar,
    FontToolBar,
)
from trufont.controls.glyphDialog import AddGlyphsDialog
from trufont.controls.glyphStatusBar import ID_ZOOM_IN, ID_ZOOM_OUT
from trufont.controls.propertiesView import makePropertiesLayout
from trufont.drawingTools.textTool import TextTool
from trufont.objects import icons
from trufont.util import clipboard, platformSpecific
from trufont.util.canvasDelete import deleteUILayerSelection
from trufont.windows.kerningWindow import KerningWindow
from trufont.windows.scriptingWindow import ScriptingWindow
from trufont.windows.loggingWindows import LoggingWindow
from tfont.converters import TFontConverter
# from tfont.objects import Glyph, Layer
from tfont.objects import Layer
from trufont.objects.undoableGlyph import UndoableGlyph
from typing import Optional
import wx
import wx.adv
from wx import GetTranslation as tr

import trufont.objects.undoManager as undomanager
import sys

import trufont.util.deco4class as deco4class

ID_DESELECT = wx.NewId()
ID_NEW_TAB = wx.NewId()
ID_NEXT_TAB = wx.NewId()
ID_PREV_TAB = wx.NewId()
ID_TABS = [
    wx.NewId(),
    wx.NewId(),
    wx.NewId(),
    wx.NewId(),
    wx.NewId(),
    wx.NewId(),
    wx.NewId(),
    wx.NewId(),
    wx.NewId(),
]
ID_TOOLS = []

ID_DEBUG_UNDOREDO = wx.NewId()

try:
    PATH = os.path.abspath(os.path.join(modulePath, "../.."))
    gitShortLog = subprocess.check_output(
        ["git", "shortlog", "-sn"], cwd=PATH, stderr=subprocess.DEVNULL
    ).decode()
except Exception:
    gitShortLog = ""


def authors():
    for line in gitShortLog.splitlines():
        elem = line.split("\t")[1]
        if not elem or elem.startswith("=?") or elem.endswith("bot"):
            continue
        yield elem


def prepareNewFont(font):
    glyphs = font.glyphs
    fontname = font.familyName
    for char in string.ascii_uppercase + string.ascii_lowercase + " ":
        name = "space" if char == " " else char
        glyphs.append(UndoableGlyph("{}-{}".format(fontname, name), unicodes=["%04X" % ord(char)]))


# @deco4class.decorator_classfunc()
class FontWindowTab(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetBackgroundColour(wx.Colour(235, 235, 235))

        self._statusBar = None
        self._view = None

    @property
    def statusBar(self):
        return self._statusBar

    @statusBar.setter
    def statusBar(self, ctrl):
        self._statusBar = ctrl
        self._makeSizer()

    @property
    def view(self):
        return self._view

    @view.setter
    def view(self, ctrl):
        self._view = ctrl
        self._makeSizer()

    def _makeSizer(self):
        statusBar = self._statusBar
        if statusBar is None:
            return
        view = self._view
        if view is None:
            return
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(view, 1, wx.EXPAND)
        sizer.AddSpacer(1)
        sizer.Add(statusBar, 0, wx.EXPAND)
        self.SetSizer(sizer)

    def close(self):
        raise NotImplementedError

    # TODO: add more things like GetTextDirection etc.?


def selectall_expand_params(obj, *args, **kwargs):
    """Used on OnSelectAllwith Nothing to """
    return obj.activeLayer    

ActiveLayerChangedEvent, EVT_ACTIVE_LAYER_CHANGED = wx.lib.newevent.NewEvent()
EVT_UPDATE_UNDOREDO = wx.lib.newevent.NewEvent()

# @deco4class.decorator_classfunc()
class FontWindow(wx.Frame):
    ACTIVE_LAYER_CHANGED = EVT_ACTIVE_LAYER_CHANGED

    def __init__(self, parent, font, path=None, logger=None, debug=False, log=False, disable_undoredo=False, 
                **kwargs):
        super().__init__(parent, **kwargs)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnCharHook)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.SetBackgroundColour(wx.Colour(212, 212, 212))
        self.SetIcon(icons.GetUserIcon("app.png", 32, 32, self))

        self._font = font
        self._path = path

        # self data for logging and undoredo actons
        self._logger = logger
        self._debug = debug
        self._disable_undoredo = disable_undoredo
        self._logwin = None
        self.dict_undomanager = {}
        # self.Bind(EVT_UPDATE_UNDOREDO, self.OnUpdateUndoRedoMenu)

        self.toolBar = FontToolBar(self)

        self.tabBar = w = FontTabBar(self, font)
        w.Bind(w.TAB_CHANGED, self.OnTabChanged)
        w.Bind(w.TAB_REMOVED, self.OnTabRemoved)

        self.bookCtrl = wx.Simplebook(self)
        tab = FontWindowTab(self.bookCtrl)

        # undoredo for this font
        tab.undoredo = undomanager.UndoManager(self._title, self._logger)

        self.cellView = w = GlyphCellView(tab)
        self.cellView.glyphs = font._glyphs
        self.cellView.SetFocus()
        w.Bind(w.GLYPH_ACTIVATED, self.OnGlyphActivated)
        w.Bind(w.SELECTION_CHANGED, self.OnSelectionChanged)

        statusBar = FontStatusBar(tab)
        statusBar.OnCountChanged(len(font.glyphs))
        # slider = wx.Slider(statusBar)
        # slider.SetSize(150, 10)
        # slider.CenterOnParent(wx.VERTICAL)

        tab.statusBar = statusBar
        tab.view = self.cellView
        self.bookCtrl.ShowNewPage(tab)

        contentSizer = wx.BoxSizer(wx.VERTICAL)
        contentSizer.Add(self.tabBar, 0, wx.EXPAND)
        contentSizer.Add(self.bookCtrl, 1, wx.EXPAND)
        propertiesSizer = makePropertiesLayout(self, font)
        self.Bind(
            self.ACTIVE_LAYER_CHANGED,
            propertiesSizer.GetChildren()[-1].GetWindow().OnActiveLayerChanged,
        )
        workspSizer = wx.BoxSizer(wx.HORIZONTAL)
        workspSizer.Add(self.toolBar, 0, wx.EXPAND)
        workspSizer.AddSpacer(1)
        workspSizer.Add(contentSizer, 1, wx.EXPAND)
        workspSizer.AddSpacer(1)
        workspSizer.Add(propertiesSizer, 0, wx.EXPAND)

        mainSizer = workspSizer
        # Set sizer to honor minimum size, then resize to our preferred value
        self.SetSizerAndFit(mainSizer)

        if self._debug:
            self.SetSize((400, 700))
            self.SetPosition((900, 100))
        else:
            size = kwargs.get("size", (1262, 800))
            self.SetSize(size)

        self.setupAccelerators()
        self.setupMenuBar()
        self.updateTitle()

        trufont.TruFont.addObserver("updateUI", self)

        self.path = None
        
    @property
    def activeLayer(self) -> Optional[Layer]:
        view = self.bookCtrl.GetCurrentPage().view
        return view.activeLayer

    @activeLayer.setter
    def activeLayer(self, layer):
        view = self.bookCtrl.GetCurrentPage().view
        if view is not self.cellView:
            view.activeLayer = layer

    @property
    def currentTab(self):
        return self.bookCtrl.GetCurrentPage()

    @property
    def font(self):
        return self._font

    @property
    def tabs(self):
        bookCtrl = self.bookCtrl
        tabs = []
        for i in range(bookCtrl.GetPageCount()):
            tabs.append(bookCtrl.GetPage(i))
        return tabs

    @property
    def _title(self):
        path = self._path
        if path is not None:
            return os.path.basename(path.rstrip(".tfont"))
        return self._font.familyName

    def newTab(self, text):
        canvas = self._newTab()
        canvas.text = text

    def _newTab(self, glyph=None):
        self.bookCtrl.Freeze()
        tab = FontWindowTab(self.bookCtrl)
        canvas = GlyphCanvasView(tab, self._font)
        # remove this the glyph arg and freeze/thaw once we have wx3.1
        if glyph is not None:
            canvas.textCursor.insertGlyph(glyph)
        #
        statusBar = GlyphStatusBar(tab, canvas)
        statusBar.Bind(
            statusBar.ZOOM_MODIFIED, partial(self.OnChangeZoom, 1), id=ID_ZOOM_IN
        )
        statusBar.Bind(
            statusBar.ZOOM_MODIFIED, partial(self.OnChangeZoom, -1), id=ID_ZOOM_OUT
        )
        tab.statusBar = statusBar
        tab.view = canvas
        self.bookCtrl.ShowNewPage(tab)
        self.bookCtrl.Thaw()
        #
        self.tabBar.addCanvasTab(canvas)
        # set an undoredo manager to that new glyph 
        if glyph:
            # may be undoredo already stores in local dict ?
            if glyph.name not in self.dict_undomanager:
                glyph.frame = self
                glyph.debug = self._debug
                glyph.disable_undoredo = self._disable_undoredo
                self.dict_undomanager[glyph.name] = glyph.get_undomanager()
                self._logger.debug("UNDOREDO_LOAD: Append in dict from UndoableGlyph ('{}')".format(glyph.name))
                if self._debug:
                    self._logger.debug("UNDOREDO_LOAD: Load undoredo stack - Layer {}".format(self.activeLayer))
                    glyph.load_from_undomanager(self.activeLayer)
            tab.undoredo = glyph.get_undomanager()
        return canvas

    def save(self, path=None):
        if path is None:
            path = self._path
        if path is None:
            self.OnSaveAs(None)
        TFontConverter().save(self._font, path)

    def close(self):
        self.Close()

    #

    def resetToolBar(self):
        self.toolBar.resetCurrentTool()

    def updateTitle(self):
        title = self._title
        if platformSpecific.appNameAndStarInTitle():
            app = wx.GetApp()
            star = "*" * self._font.modified
            title = f"{star}{title} – {app.GetAppDisplayName()}"
        self.SetTitle(title)

    # ----------
    # wx methods
    # ----------

    def setupAccelerators(self):
        table = [
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D"), ID_DESELECT),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("T"), ID_NEW_TAB),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_TAB, ID_NEXT_TAB),
            wx.AcceleratorEntry(
                wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_TAB, ID_PREV_TAB
            ),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("W"), wx.ID_CLOSE),
        ]
        base = ord("1")
        for idx, ID_TAB in enumerate(ID_TABS):
            table.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, base + idx, ID_TAB))
            self.Bind(wx.EVT_MENU, partial(self.OnChangeTab, idx), id=ID_TAB)
        self.SetAcceleratorTable(wx.AcceleratorTable(table))
        # NOTE for when we want to re-enter this function: we only need to bind
        # once. the ids stay the same
        self.Bind(wx.EVT_MENU, self.OnDeselect, id=ID_DESELECT)
        self.Bind(wx.EVT_MENU, self.OnOpenTab, id=ID_NEW_TAB)
        self.Bind(wx.EVT_MENU, partial(self.OnShiftTab, 1), id=ID_NEXT_TAB)
        self.Bind(wx.EVT_MENU, partial(self.OnShiftTab, -1), id=ID_PREV_TAB)
        self.Bind(wx.EVT_MENU, self.OnCloseTab, id=wx.ID_CLOSE)

    def setupMenuBar(self):
        fileMenu = wx.Menu()
        self.Bind(wx.EVT_MENU, self.OnNew, fileMenu.Append(wx.ID_NEW))
        self.Bind(wx.EVT_MENU, self.OnOpen, fileMenu.Append(wx.ID_OPEN))
        recentFiles = wx.Menu()
        fileMenu.Append(wx.ID_ANY, tr("Open &Recent"), recentFiles)
        fileMenu.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.OnSave, fileMenu.Append(wx.ID_SAVE))
        self.Bind(
            wx.EVT_MENU,
            self.OnSaveAs,
            fileMenu.Append(wx.ID_SAVEAS, tr("Save &As...\tCtrl+Shift+S")),
        )
        self.Bind(
            wx.EVT_MENU,
            self.OnRevert,
            fileMenu.Append(wx.ID_REVERT_TO_SAVED, tr("&Revert")),
        )
        fileMenu.AppendSeparator()
        item = fileMenu.Append(wx.ID_ANY, tr("&Export...\tCtrl+E"))
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnExport, item)
        self.Bind(wx.EVT_MENU, self.OnExit, fileMenu.Append(wx.ID_EXIT))

        editMenu = wx.Menu()
        item = editMenu.Append(wx.ID_UNDO)
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnUndo, item)
        # store menu_undo 
        self.menu_undo = item 
        item = editMenu.Append(wx.ID_REDO)
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnRedo, item)
        # store menu_undo 
        self.menu_redo = item 

        # undoredo debug menu 
        if self._debug:
            self._logger.debug("UNDOREDO: Append an debug menu")
            editMenu.AppendSeparator()
            self.menu_undoredo = editMenu.Append(ID_DEBUG_UNDOREDO, tr("DEBUG: undoredo"))
            self.menu_undoredo.Enable(True)

        editMenu.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.OnCut, editMenu.Append(wx.ID_CUT))
        self.Bind(wx.EVT_MENU, self.OnCopy, editMenu.Append(wx.ID_COPY))
        self.Bind(wx.EVT_MENU, self.OnPaste, editMenu.Append(wx.ID_PASTE))
        self.Bind(
            wx.EVT_MENU,
            self.OnSelectAll,
            editMenu.Append(wx.ID_SELECTALL, tr("Select &All\tCtrl+A")),
        )
        item = editMenu.Append(wx.ID_FIND, tr("Find...\tCtrl+F"))
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnFind, item)
        editMenu.AppendSeparator()
        item = editMenu.Append(wx.ID_ANY, tr("Settings..."))
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnSettings, item)

        fontMenu = wx.Menu()
        # could be in the window menu? --> and this menu can be called glyphs
        # or the opposite, kerning could be in this menu
        # NO -> kerning always shows the current window where this is specific
        item = fontMenu.Append(wx.ID_ANY, tr("Font &Info\tCtrl+Alt+I"))
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnFontInfo, item)
        fontMenu.AppendSeparator()
        self.Bind(
            wx.EVT_MENU,
            self.OnAddGlyphs,
            fontMenu.Append(wx.ID_ANY, tr("Add Glyphs...\tCtrl+G")),
        )

        viewMenu = wx.Menu()
        self.Bind(
            wx.EVT_MENU,
            partial(self.OnChangeZoom, 1),
            viewMenu.Append(ID_ZOOM_IN, tr("Zoom In\tCtrl++")),
        )
        self.Bind(
            wx.EVT_MENU,
            partial(self.OnChangeZoom, -1),
            viewMenu.Append(ID_ZOOM_OUT, tr("Zoom Out\tCtrl+-")),
        )
        self.Bind(
            wx.EVT_MENU,
            self.OnResetZoom,
            viewMenu.Append(wx.ID_ANY, tr("Reset Zoom\tCtrl+0")),
        )
        viewMenu.AppendSeparator()
        self.Bind(
            wx.EVT_MENU,
            partial(self.OnShiftGlyph, 1),
            viewMenu.Append(wx.ID_ANY, tr("Next Glyph\tEnd")),
        )
        self.Bind(
            wx.EVT_MENU,
            partial(self.OnShiftGlyph, -1),
            viewMenu.Append(wx.ID_ANY, tr("Previous Glyph\tHome")),
        )
        viewMenu.AppendSeparator()
        item = viewMenu.Append(
            wx.ID_ANY, tr("Show Points\tCtrl+Shift+P"), kind=wx.ITEM_CHECK
        )
        item.Check(True)
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnAttributeChange, item)
        item = viewMenu.Append(
            wx.ID_ANY, tr("Show Metrics\tCtrl+Shift+M"), kind=wx.ITEM_CHECK
        )
        item.Check(True)
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnAttributeChange, item)
        item = viewMenu.Append(wx.ID_ANY, tr("Show Images"), kind=wx.ITEM_CHECK)
        item.Check(True)
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnAttributeChange, item)
        item = viewMenu.Append(
            wx.ID_ANY, tr("Show Guidelines\tCtrl+Shift+G"), kind=wx.ITEM_CHECK
        )
        item.Check(True)
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnAttributeChange, item)

        windowMenu = wx.Menu()
        self.Bind(
            wx.EVT_MENU,
            self.OnKerning,
            windowMenu.Append(wx.ID_ANY, tr("Kerning\tCtrl+Alt+K")),
        )
        self.Bind(
            wx.EVT_MENU,
            self.OnScripting,
            windowMenu.Append(wx.ID_ANY, tr("Scripting\tCtrl+Alt+R")),
        )
        if self._debug:
            windowMenu.AppendSeparator()
            self.Bind(wx.EVT_MENU,
			          self.OnLogging,
		              windowMenu.Append(wx.ID_ANY, tr("Logging...\tCtrl+Alt+L")),
            )
        windowMenu.AppendSeparator()
        item = windowMenu.Append(wx.ID_ANY, tr("Output\tCtrl+Alt+O"))
        item.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnOutput, item)

        helpMenu = wx.Menu()
        self.Bind(
            wx.EVT_MENU,
            self.OnDocumentation,
            helpMenu.Append(wx.ID_ANY, tr("Documentation")),
        )
        self.Bind(
            wx.EVT_MENU,
            self.OnReportIssue,
            helpMenu.Append(wx.ID_ANY, tr("Report an Issue")),
        )
        helpMenu.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.OnAbout, helpMenu.Append(wx.ID_ABOUT))

        # recent files should show 9 files with no numbers followed by
        # a separator and a Clear Menu entry
        app = wx.GetApp()
        app.fileHistory.UseMenu(recentFiles)
        app.fileHistory.AddFilesToMenu(recentFiles)
        self.Bind(
            wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9
        )
        recentFiles.AppendSeparator()
        recentFiles.Append(wx.ID_CLEAR, tr("Clear Menu"))

        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, wx.GetStockLabel(wx.ID_FILE))
        menuBar.Append(editMenu, wx.GetStockLabel(wx.ID_EDIT))
        menuBar.Append(fontMenu, tr("&Font"))
        menuBar.Append(viewMenu, tr("&View"))
        menuBar.Append(windowMenu, tr("&Window"))
        menuBar.Append(helpMenu, wx.GetStockLabel(wx.ID_HELP))
        self.SetMenuBar(menuBar)
# 

    def OnUpdateUndoRedoMenu(self, undoredo: undomanager.UndoManager):
        """ update redo/undo status menu on each activation """
        self._logger.debug("UNDOREDO: OnUpdateUndoRedoMenu {}".format(undoredo.str_state()))
        self.menu_undo.Enable(undoredo.can_undo())
        if undoredo.can_undo():
            self.menu_undo.SetText("Undo '{}'\tCtrl+Z".format(undoredo.next_undo_operation()))
        else:
            self.menu_undo.SetText("Undo\tCtrl+Z") 

        self.menu_redo.Enable(undoredo.can_redo())
        if undoredo.can_redo():
            self.menu_redo.SetText("Redo '{}'\tCtrl+Shift+Z".format(undoredo.next_redo_operation()))
        else:
            self.menu_redo.SetText("Redo\tCtrl+Shift+Z") 

        if self._debug:
            self.menu_undoredo.SetText("DEBUG: " + undoredo.str_state())

         
    # self

    def OnCharHook(self, event):
        focusWindow = wx.Window.FindFocus()
        # clear to engage?
        # we could even unsub from this event on focus out and sub on focus in
        if isinstance(focusWindow, GlyphCanvasView) and focusWindow._font is self._font:
            # toolbar
            self.toolBar.DoProcessCharHook(event)
            if not event.GetSkipped():
                return
        event.Skip()

    def OnUpdateUI(self):
        # self.cellView.glyphs = self._font._glyphs
        self.updateTitle()

    def OnClose(self, event):
        if self._queryCanDiscard():
            event.Skip()
        else:
            if event.CanVeto():
                event.Veto()
            else:
                pass  # save unsaved file to a standard location

    def OnFileHistory(self, event):
        fileNum = event.GetId() - wx.ID_FILE1
        path = wx.GetApp().fileHistory.GetHistoryFile(fileNum)
        trufont.TruFont.openFont(path)

    # controls

    def OnGlyphActivated(self, event):
        glyph = event.glyph
        # look for existing tab
        for i in range(self.bookCtrl.GetPageCount()):
            if not i:
                continue
            canvas = self.bookCtrl.GetPage(i).view
            layers = canvas._layoutManager.layers
            if len(layers) == 1 and layers[0].glyph == glyph:
                self.tabBar.setCurrentTab(i)
                return
        canvas = self._newTab(glyph)
        # canvas.textCursor.insertGlyph(glyph)

    def OnSelectionChanged(self, event):
        statusBar = self.bookCtrl.GetPage(0).statusBar
        statusBar.OnSelectionChanged(len(event.selection))
        wx.PostEvent(self, ActiveLayerChangedEvent())

    def OnTabChanged(self, event):
        self.bookCtrl.Freeze()
        self.bookCtrl.ChangeSelection(event.index)
        view = self.bookCtrl.GetCurrentPage().view
        self.toolBar.setParentControl(view)
        view.SetFocus()
        # activate the undomanager of current tab (Here a glyph or the font) 
        tab = self.bookCtrl.GetCurrentPage()
        try: 
            # wx.SendEvent(self, EVT_UPDATE_UNDOREDO)
            self.OnUpdateUndoRedoMenu(tab.undoredo)
        except Exception as e:
            self._logger.debug("UNDOREDO: exception on {}".format(str(e)))

        self.bookCtrl.Thaw()
        wx.PostEvent(self, ActiveLayerChangedEvent())

    def OnTabRemoved(self, event):
        self.bookCtrl.RemovePage(event.index)

    def _queryCanDiscard(self) -> bool:
        font = self._font
        if not font.modified:
            return True
        text = (
            tr("Do you want to save your changes to “%s” before closing?") % self._title
        )
        caption = tr("Your changes will be lost if you don’t save them.")
        with wx.MessageDialog(
            self, text, style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
        ) as dialog:
            dialog.SetExtendedMessage(caption)
            ret = dialog.ShowModal()
        if ret == wx.ID_YES:
            if self.path:
                self.save(self.path)
            else:
                self.OnSaveAs(None)
        elif ret == wx.ID_NO:
            return True
        return False

    # shortcuts

    def OnChangeTab(self, index, event):
        tabBar = self.tabBar
        if index >= tabBar.count():
            return
        tabBar.setCurrentTab(index)

    def OnCloseTab(self, event):
        view = self.currentTab.view
        if view is not self.cellView:
            self.tabBar.removeCanvasTab(view)

    def OnDeselect(self, event):
        view = self.currentTab.view
        if view is self.cellView:
            view.selection = set()
        else:
            self.activeLayer.clearSelection()
            trufont.TruFont.updateUI()

    def OnOpenTab(self, event):
        self._newTab()
        self.toolBar.setCurrentTool(TextTool)

    def OnShiftTab(self, shift, event):
        tabBar = self.tabBar
        index = (tabBar.currentTab() + shift) % tabBar.count()
        tabBar.setCurrentTab(index)

    # ------------
    # Menu entries
    # ------------

    # File

    def OnNew(self, event):
        trufont.TruFont.newFont()

    def OnOpen(self, event):
        trufont.TruFont.openFont()

    def OnSave(self, event):
        if self.path:
            self.save(self.path)
        else:
            self.OnSaveAs(event)

    def OnSaveAs(self, event):
        with wx.FileDialog(self, tr("Save Font File"), wildcard="Font Files (*.tfont)|*.tfont",
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            self.path = dialog.GetPath()
        self.save(self.path)
        wx.GetApp().fileHistory.AddFileToHistory(self.path)
        self.updateTitle()

    def OnRevert(self, event):
        if not self._queryCanDiscard():
            return
        if self._path is not None:
            TFontConverter().open(self._path, self._font)
        else:
            self._font.__init__()
            prepareNewFont(self._font)
        trufont.TruFont.updateUI()

    def OnExport(self, event):
        raise NotImplementedError

    def OnExit(self, event):
        for window in wx.GetTopLevelWindows():
            if isinstance(window, FontWindow):
                window.Close()
        # loop again to see if user kept font windows open
        for window in wx.GetTopLevelWindows():
            if isinstance(window, FontWindow):
                return
        wx.Exit()

    # Edit

    def OnUndo(self, event):
        """ undo opertion let's go ....."""
        tab = self.bookCtrl.GetCurrentPage()
        self.Refresh()
        # try:
        #     action = tab.undoredo.undo()
        #     self._logger.debug("UNDOREDO: undo on {}".format(str(action.operation)))
        #     call_func = action.callback_undo()
        # except Exception as e:
        #     self._logger.debug("UNDOREDO: undo exception on {}".format(str(e)))

        if tab.undoredo.can_undo():
            with tab.undoredo.undo_ctx() as action:
                self._logger.debug("UNDOREDO: undo on {}".format(str(action.operation)))
                action.callback_undo()
        self.OnUpdateUndoRedoMenu(tab.undoredo)
        trufont.TruFont.updateUI()


    def OnRedo(self, event):
        tab = self.bookCtrl.GetCurrentPage()
        self.Refresh()
        # try:
        #     action = tab.undoredo.redo()
        #     self._logger.debug("UNDOREDO: redo on {}".format(str(action.operation)))
        #     action.callback_redo()
        # except Exception as e:
        #     self._logger.debug("UNDOREDO: redo exception on {}".format(str(e)))
        if tab.undoredo.can_redo():
            with tab.undoredo.redo_ctx() as action:
                self._logger.debug("UNDOREDO: redo on {}".format(str(action.operation)))
                action.callback_redo()

        self.OnUpdateUndoRedoMenu(tab.undoredo)
        trufont.TruFont.updateUI()

    def OnCut(self, event):
        layer = self.activeLayer
        if layer is None:
            return
        cellView = self.cellView
        if self.currentTab.view is cellView:
            raise NotImplementedError
        else:
            clipboard.store(layer)
            # undoredo action done in deleteUILayerSelection
            deleteUILayerSelection(layer, origin="Cut selection", breakPaths=True)
            trufont.TruFont.updateUI()

    def OnCopy(self, event):
        layer = self.activeLayer
        if layer is None:
            return
        cellView = self.cellView
        if self.currentTab.view is cellView:
            raise NotImplementedError
        else:
            clipboard.store(layer)

    def OnPaste(self, event):
        layer = self.activeLayer
        if layer is None:
            return
        cellView = self.cellView
        if self.currentTab.view is cellView:
            raise NotImplementedError
        else:
            # undoredo acion done in retrieve
            if clipboard.retrieve(layer):
                trufont.TruFont.updateUI()

    def OnSelectAll(self, event):
        cellView = self.cellView
        if self.currentTab.view is cellView:
            cellView.selectAll()
        else:
            layer = self.activeLayer
            if layer is None:
                return    
            self.OnSelectAllFromLayer(layer)

    @undomanager.layer_decorate_undo(selectall_expand_params, operation="Selection all", 
                                     paths=True, guidelines=False, components=True, anchors=True)
    def OnSelectAllFromLayer(self, layer: Layer):        
        # pathsAreSelected = True
        for path in layer.paths:
            if not path.selected:
                pathsAreSelected = False
                path.selected = True
        # if pathsAreSelected:
        for anchor in layer.anchors:
            anchor.selected = True
        for component in layer.components:
            component.selected = True
        trufont.TruFont.updateUI()

    def OnFind(self, event):
        raise NotImplementedError

    def OnSettings(self, event):
        raise NotImplementedError

    # Font

    def OnFontInfo(self, event):
        raise NotImplementedError

    def OnAddGlyphs(self, event):
        dialog = AddGlyphsDialog(self.currentTab.view, self._font)
        dialog.ShowModal()

    # View

    def OnChangeZoom(self, step, event):
        cellView = self.cellView
        view = self.currentTab.view
        if view is cellView:
            raise NotImplementedError
        else:
            newScale = view.scale * pow(1.2, step)
            view.zoom(newScale)

    def OnResetZoom(self, event):
        cellView = self.cellView
        view = self.currentTab.view
        if view is cellView:
            raise NotImplementedError
        else:
            view.fitMetrics()

    def OnShiftGlyph(self, shift, event):
        cellView = self.cellView
        view = self.currentTab.view
        if view is cellView:
            activeCell = cellView.activeCell
            if activeCell is None:
                return
            newIndex = activeCell + shift
            if newIndex < 0 or newIndex >= len(cellView.glyphs):
                return
            cellView.selection = {newIndex}
        else:
            textCursor = view.textCursor
            index = textCursor.popPreviousChar()
            if index is None:
                return
            glyphs = self._font.glyphs
            index = (index + shift) % len(glyphs)
            textCursor.insertGlyph(glyphs[index])

    def OnAttributeChange(self, event):
        raise NotImplementedError

    # Window

    def OnKerning(self, event):
        KerningWindow(self, self._font).Show()

    def OnScripting(self, event):
        ScriptingWindow(self).Show()

    def OnLogging(self, event):
        if not self._logwin:
            self._logwin = LoggingWindow(self, self._logger)
            self._logwin.Show()
        else:
            self._logwin.SetFocus()

    def OnloggingClosed(self):
        self._logwin = None

    def OnOutput(self, event):
        raise NotImplementedError

    # Help

    def OnDocumentation(self, event):
        wx.LaunchDefaultBrowser("http://trufont.github.io/")

    def OnReportIssue(self, event):
        wx.LaunchDefaultBrowser("https://github.com/trufont/trufont/issues/new")

    def OnAbout(self, event):
        name = wx.GetApp().GetAppDisplayName()
        info = wx.adv.AboutDialogInfo()
        info.SetIcon(icons.GetUserIcon("app.png", 128, 128, self))
        info.SetVersion(__version__)
        info.SetDescription(tr("%s is a streamlined and hackable font editor.") % name)
        info.SetCopyright("(C) 2018 The TruFont Project Developers")
        info.SetLicense(
            "Licensed under the Mozilla Public License, Version 2.0.\n"
            "\n"
            "If a copy of the MPL was not distributed with this program,\n"
            "you can obtain one at <https://mozilla.org/MPL/2.0/>."
        )
        info.SetWebSite("https://trufont.github.io", tr("TruFont website"))
        info.SetDevelopers(list(authors()))
        wx.adv.AboutBox(info, self)



