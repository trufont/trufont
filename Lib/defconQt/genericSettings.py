from PyQt5.QtWidgets import QMenu
from functools import partial


class GenericSettings(object):

    def __init__(self, title, parent, callback):
        # super().__init__()
        self._menuWidget = QMenu(title, parent)
        self._actions = {}
        self._callback = callback
        for key, item in self._items:
            self._addAction(key, *item)

        if(self._presets):
            self._menuWidget.addSeparator()
            for i, presets in enumerate(self._presets):
                self._addPresetAction(i, *presets)

    _items = {}
    _presets = tuple()

    @property
    def menuWidget(self):
        return self._menuWidget

    def _addAction(self, key, label, checked):
        action = self._menuWidget.addAction(label,
                                            partial(self._callback, key))
        action.setCheckable(True)
        action.setChecked(checked)
        self._actions[key] = action

    def _addPresetAction(self, index, label, presets, **args):
        self._menuWidget.addAction(label, partial(self._setPreset, index))

    def _setPreset(self, index):
        _, data = self._presets[index]
        for key, value in data.items():
            action = self._actions[key]
            action.blockSignals(True)
            action.setChecked(value)
            action.blockSignals(False)
        self._callback()

    def __setattr__(self, name, value):
        if name.startswith('_'):
            self.__dict__[name] = value
            return
        raise AttributeError('It\'s not allowed to set attributes here.', name)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self._actions:
            raise AttributeError(name)
        return self._actions[name].isChecked()
