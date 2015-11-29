from defconQt.dialogs.gotoDialog import GotoDialog


class AddComponentDialog(GotoDialog):

    def __init__(self, *args, **kwargs):
        super(AddComponentDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle("Add component…")
        self._sortedGlyphs.remove(args[0].name)
        self.updateGlyphList(False)
