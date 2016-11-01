"""
Windows that want to plug-in their own menu entries must implement

- setupMenu(menuBar)
- menuBar()
- setMenuBar(menuBar)

"""
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QMenuBar
from trufont.tools import platformSpecific

MAX_RECENT_FILES = 10


class MenuBar(QMenuBar):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._spawnElementsHint = True

    def shouldSpawnElements(self):
        return self.parent() is None or self._spawnElementsHint

    def spawnElementsHint(self):
        return self._spawnElementsHint

    def setSpawnElementsHint(self, value):
        self._spawnElementsHint = value

    def fetchMenu(self, title):
        title = _trMenuString(title)
        # cache lookup
        child = None
        for child_ in self.children():
            if not isinstance(child_, QMenu):
                continue
            if child_.title() == title:
                child = child_
        if child is not None:
            return child
        # spawn
        menu = Menu(title, self)
        if self.shouldSpawnElements():
            self.addMenu(menu)
        return menu

    def resetState(self):
        for menu in self.children():
            if not isinstance(menu, QMenu):
                continue
            menu.resetState()


class Menu(QMenu):

    def shouldSpawnElements(self):
        parent = self.parent()
        if parent is not None:
            return parent.shouldSpawnElements()
        return False

    def fetchAction(self, text, callback=None, shortcut=None):
        if shortcut is None:
            shortcut = _shortcuts.get(text)
        text = _trMenuString(text)
        action = None
        # cache lookup
        action = None
        for action_ in self.actions():
            if action_.text() == text:
                action = action_
        # spawn
        if action is None:
            action = QAction(text, self)
            if self.shouldSpawnElements():
                self.addAction(action)
        # connect
        action.setEnabled(True)
        try:
            action.triggered.disconnect()
        except TypeError:
            pass
        if callback is not None:
            action.triggered.connect(lambda: callback())
        action.setShortcut(QKeySequence(shortcut))
        return action

    fetchMenu = MenuBar.fetchMenu

    def resetState(self):
        self._ready = True
        # TODO: reset submenus too?
        for action in self.actions():
            action.setEnabled(False)


class Entries(object):
    File = "&File"
    File_New = "&New…"
    File_Open = "&Open…"
    File_Open_Recent = "Open &Recent"
    File_Import = "&Import…"
    File_Save = "&Save"
    File_Save_As = "Save &As…"
    File_Save_All = "Save A&ll"
    File_Close = "&Close"
    File_Reload = "&Revert"
    File_Export = "&Export…"
    File_Exit = "E&xit"

    Edit = "&Edit"
    Edit_Undo = "&Undo"
    Edit_Redo = "&Redo"
    Edit_Cut = "C&ut"
    Edit_Copy = "&Copy"
    Edit_Copy_As_Component = "Copy &As Component"
    Edit_Paste = "&Paste"
    Edit_Clear = "Cl&ear"
    Edit_Select_All = "&Select All"
    Edit_Find = "&Find…"
    Edit_Settings = "&Settings…"

    View = "&View"
    View_Zoom_In = "Zoom &In"
    View_Zoom_Out = "Zoom &Out"
    View_Reset_Zoom = "&Reset Zoom"
    View_Next_Glyph = "&Next Glyph"
    View_Previous_Glyph = "&Previous Glyph"

    Font = "F&ont"
    Font_Font_Info = "Font &Info"
    Font_Font_Features = "Font &Features"
    Font_Add_Glyphs = "&Add Glyphs…"
    Font_Sort = "&Sort…"

    Scripts = "&Scripts"
    Scripts_Build_Extension = "&Build Extension…"

    # TODO: remove inspector and metrics
    Window = "&Window"
    Window_Minimize = "&Minimize"
    Window_Minimize_All = "Minimize &All"
    Window_Zoom = "&Zoom"
    Window_Inspector = "&Inspector"
    Window_Groups = "&Groups"
    Window_Kerning = "&Kerning"
    Window_Metrics = "M&etrics"
    Window_Scripting = "&Scripting"
    Window_Output = "&Output"

    Help = "&Help"
    Help_Documentation = "&Documentation"
    Help_Report_An_Issue = "&Report an Issue"
    Help_About = "&About"


_shortcuts = {
    Entries.File_New: QKeySequence.New,
    Entries.File_Open: QKeySequence.Open,
    Entries.File_Save: QKeySequence.Save,
    Entries.File_Save_As: QKeySequence.SaveAs,
    Entries.File_Close: platformSpecific.closeKeySequence(),
    Entries.File_Export: "Ctrl+E",
    Entries.File_Exit: QKeySequence.Quit,

    Entries.Edit_Undo: QKeySequence.Undo,
    Entries.Edit_Redo: QKeySequence.Redo,
    Entries.Edit_Cut: QKeySequence.Cut,
    Entries.Edit_Copy: QKeySequence.Copy,
    Entries.Edit_Copy_As_Component: "Ctrl+Alt+C",
    Entries.Edit_Paste: QKeySequence.Paste,
    Entries.Edit_Select_All: QKeySequence.SelectAll,
    Entries.Edit_Find: QKeySequence.Find,

    Entries.View_Zoom_In: QKeySequence.ZoomIn,
    Entries.View_Zoom_Out: QKeySequence.ZoomOut,
    Entries.View_Reset_Zoom: "Ctrl+0",
    Entries.View_Next_Glyph: "End",
    Entries.View_Previous_Glyph: "Home",

    Entries.Font_Font_Info: "Ctrl+Alt+I",
    Entries.Font_Font_Features: "Ctrl+Alt+F",
    Entries.Font_Add_Glyphs: "Ctrl+G",

    Entries.Window_Minimize: "Ctrl+M",
    Entries.Window_Inspector: "Ctrl+I",
    Entries.Window_Groups: "Ctrl+Alt+G",
    Entries.Window_Kerning: "Ctrl+Alt+K",
    Entries.Window_Metrics: "Ctrl+Alt+S",
    Entries.Window_Scripting: "Ctrl+Alt+R",
    Entries.Window_Output: "Ctrl+Alt+O",
}


def globalMenuBar():
    menuBar = MenuBar()
    fileMenu = menuBar.fetchMenu(Entries.File)
    fileMenu.fetchAction(Entries.File_New)
    fileMenu.fetchAction(Entries.File_Open)
    fileMenu.fetchMenu(Entries.File_Open_Recent)
    # no-op, caller will maintain this
    if not platformSpecific.mergeOpenAndImport():
        fileMenu.fetchAction(Entries.File_Import)
    fileMenu.addSeparator()
    fileMenu.fetchAction(Entries.File_Save)
    fileMenu.fetchAction(Entries.File_Save_As)
    fileMenu.fetchAction(Entries.File_Save_All)
    fileMenu.fetchAction(Entries.File_Close)
    fileMenu.fetchAction(Entries.File_Reload)
    fileMenu.addSeparator()
    fileMenu.fetchAction(Entries.File_Export)
    fileMenu.fetchAction(Entries.File_Exit)

    editMenu = menuBar.fetchMenu(Entries.Edit)
    editMenu.fetchAction(Entries.Edit_Undo)
    editMenu.fetchAction(Entries.Edit_Redo)
    editMenu.addSeparator()
    editMenu.fetchAction(Entries.Edit_Cut)
    editMenu.fetchAction(Entries.Edit_Copy)
    editMenu.fetchAction(Entries.Edit_Copy_As_Component)
    editMenu.fetchAction(Entries.Edit_Paste)
    editMenu.fetchAction(Entries.Edit_Clear)
    editMenu.fetchAction(Entries.Edit_Select_All)
    editMenu.fetchAction(Entries.Edit_Find)
    editMenu.addSeparator()
    editMenu.fetchAction(Entries.Edit_Settings)
    menuBar.addMenu(editMenu)

    viewMenu = menuBar.fetchMenu(Entries.View)
    viewMenu.fetchAction(Entries.View_Zoom_In)
    viewMenu.fetchAction(Entries.View_Zoom_Out)
    viewMenu.fetchAction(Entries.View_Reset_Zoom)
    viewMenu.addSeparator()
    viewMenu.fetchAction(Entries.View_Next_Glyph)
    viewMenu.fetchAction(Entries.View_Previous_Glyph)

    fontMenu = menuBar.fetchMenu(Entries.Font)
    fontMenu.fetchAction(Entries.Font_Font_Info)
    fontMenu.fetchAction(Entries.Font_Font_Features)
    fontMenu.addSeparator()
    fontMenu.fetchAction(Entries.Font_Add_Glyphs)
    fontMenu.fetchAction(Entries.Font_Sort)

    menuBar.fetchMenu(Entries.Scripts)
    # no-op, caller will maintain this

    windowMenu = menuBar.fetchMenu(Entries.Window)
    if platformSpecific.windowCommandsInMenu():
        windowMenu.fetchAction(Entries.Window_Minimize)
        windowMenu.fetchAction(Entries.Window_Minimize_All)
        windowMenu.fetchAction(Entries.Window_Zoom)
        windowMenu.addSeparator()
    windowMenu.fetchAction(Entries.Window_Inspector)
    windowMenu.addSeparator()
    windowMenu.fetchAction(Entries.Window_Groups)
    windowMenu.fetchAction(Entries.Window_Kerning)
    windowMenu.fetchAction(Entries.Window_Metrics)
    windowMenu.fetchAction(Entries.Window_Scripting)
    windowMenu.addSeparator()
    windowMenu.fetchAction(Entries.Window_Output)

    helpMenu = menuBar.fetchMenu(Entries.Help)
    helpMenu.fetchAction(Entries.Help_Documentation)
    helpMenu.fetchAction(Entries.Help_Report_An_Issue)
    helpMenu.addSeparator()
    helpMenu.fetchAction(Entries.Help_About)

    return menuBar


def _trMenuString(string):
    return QApplication.translate("AppMenu", string)
