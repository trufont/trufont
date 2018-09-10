from trufont.objects import icons
import wx
from wx import dataview, GetTranslation as tr


# should be kerning key, not necessarily a group
class LeftKerningGroup:
    __slots__ = "key",

    def __init__(self, key):
        self.key = key


class RightKerningGroup:
    __slots__ = "key", "lkey", "parent"

    def __init__(self, key, lkey, parent):
        self.key = key
        self.lkey = lkey
        self.parent = parent

    @property
    def value(self):
        return self._value


class KerningModel(dataview.PyDataViewModel):

    def __init__(self, data):
        super().__init__()
        self.data = data

    #def GetAttr(self, item, col, attr):
    #    pass

    def GetChildren(self, parent, children):
        if not parent:
            keys = self.data.keys()
            for key in keys:
                children.append(self.ObjectToItem(LeftKerningGroup(key)))
            return len(keys)

        node = self.ItemToObject(parent)
        if node.__class__ is LeftKerningGroup:
            lkey = node.key
            keys = self.data[lkey].keys()
            for key in keys:
                children.append(
                    self.ObjectToItem(RightKerningGroup(key, lkey, node)))
            return len(keys)
        return 0

    def GetColumnCount(self):
        return 2

    def GetColumnType(self, column):
        return "integer" if column else "string"

    def GetParent(self, item):
        if not item:
            return dataview.NullDataViewItem

        node = self.ItemToObject(item)
        cls = node.__class__
        if cls is LeftKerningGroup:
            return dataview.NullDataViewItem
        elif cls is RightKerningGroup:
            # I think this happens rarely enough that we neednt cache parent
            return node.parent

    def GetValue(self, item, column):
        node = self.ItemToObject(item)
        if column:
            return self.data[node.lkey][node.key]
        else:
            return node.key

    def IsContainer(self, item):
        return not item or self.ItemToObject(
            item).__class__ is LeftKerningGroup


class KerningWindow(wx.Frame):

    def __init__(self, parent, font):
        super().__init__(parent)
        self.SetIcon(icons.GetUserIcon("app.png", 32, 32, self))
        self.SetTitle(tr("Kerning – %s") % wx.GetApp().GetAppDisplayName())

        self.dataCtrl = dataview.DataViewCtrl(
            self, style=dataview.DV_NO_HEADER)
        data = font.selectedMaster.hKerning
        self.dataModel = KerningModel(data)
        self.dataCtrl.AssociateModel(self.dataModel)
        col = self.dataCtrl.AppendTextColumn(wx.EmptyString, 0)
        self.dataCtrl.AppendTextColumn(wx.EmptyString, 1)
        #col.Sortable = True

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.dataCtrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetSize((300, 520))
        col.SetWidth(self.dataCtrl.GetClientSize()[0])
