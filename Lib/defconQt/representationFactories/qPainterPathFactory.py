# -*- coding: utf-8 -*-
"""
The *qPainterPathFactory* submodule
-----------------------------

The *qPainterPathFactory* submodule provides a QPainterPath_ representation of
a Glyph_’s outline.

QPainterPath_ is the Qt class for Bézier paths. It accomodates cubic or
quadratic outlines and has a pen interface.

You can then draw such paths on screen with the QPainter_ method
``drawPath()``.

.. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
.. _QPainter: http://doc.qt.io/qt-5/qpainter.html
.. _QPainterPath: http://doc.qt.io/qt-5/qpainterpath.html
"""
from __future__ import absolute_import
from fontTools.pens.qtPen import QtPen
from PyQt5.QtCore import Qt


def QPainterPathFactory(glyph):
    pen = QtPen(glyph.layer)
    glyph.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
    return pen.path
