# -*- coding: utf-8 -*-
"""
The *baseWindows* submodule
---------------------------

The *baseWindows* submodule provides base implementations of top-level windows.

Due to some implementations details of memory management between Python and Qt,
parentless windows normally end up being deleted by the `Garbage Collector`_ of
Python and disappear, unless a reference to them is stored in a main namespace.

The base windows presented here take care of this problem automatically, and
should be used for spawning top-level windows (in scripting, notably).

- :class:`BaseWindow` is a QWidget_ top-level window
- :class:`BaseMainWindow` a QMainWindow_ top-level window

Both are used the same as their Qt widget parents, e.g.:

>>> from defconQt.windows.baseWindows import BaseWindow
>>> from PyQt5.QtWidgets import QLabel
>>> window = BaseWindow()
>>> label = QLabel("Hello World!", window)
>>> window.show()

Note: a QMainWindow_ is a QWidget subclass that has a predefined layout. See
its documentation for more details.

.. _QWidget: http://doc.qt.io/qt-5/qwidget.html
.. _QMainWindow: http://doc.qt.io/qt-5/qmainwindow.html
.. _`Garbage Collector`: https://en.wikipedia.org/wiki/Garbage_collection_(computer_science)
"""
from __future__ import absolute_import
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget


def _bootstrapGCCache(self):
    app = QApplication.instance()
    if not hasattr(app, "_windowCache"):
        app._windowCache = set()
    app._windowCache.add(self)


def _flushGCCache(self):
    app = QApplication.instance()
    try:
        app._windowCache.remove(self)
    except KeyError:
        # if self.close() is called more than once we'll end up
        # here. that's fine
        pass


class BaseMainWindow(QMainWindow):
    """
    A QMainWindow top-level window that keeps itself alive until it’s closed.

    See QMainWindow_ documentation for the list of available methods.

    .. _QMainWindow: http://doc.qt.io/qt-5/qmainwindow.html
    """

    def __init__(self, parent=None, flags=Qt.Window):
        super(BaseMainWindow, self).__init__(parent, flags)
        self.setAttribute(Qt.WA_DeleteOnClose)
        _bootstrapGCCache(self)

    def closeEvent(self, event):
        super(BaseMainWindow, self).closeEvent(event)
        if event.isAccepted():
            _flushGCCache(self)


class BaseWindow(QWidget):
    """
    A QWidget top-level window that keeps itself alive until it’s closed.

    Sets Qt.Window as default *flags* parameter.

    See QWidget_ documentation for the list of available methods.

    .. _QWidget: http://doc.qt.io/qt-5/qwidget.html
    """

    def __init__(self, parent=None, flags=Qt.Window):
        super(BaseWindow, self).__init__(parent, flags)
        self.setAttribute(Qt.WA_DeleteOnClose)
        _bootstrapGCCache(self)

    def closeEvent(self, event):
        super(BaseWindow, self).closeEvent(event)
        if event.isAccepted():
            _flushGCCache(self)
