"""
Icon database, issues drawing commands. PathButton is a consumer.
"""
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QColor, QPainterPath, QTransform

from trufont.objects.pathIcon import PathIcon

_listIconsStrokeColor = QColor(90, 90, 90)
_sidebarIconsFillColor = QColor(187, 187, 187)
_sidebarIconsStrokeColor = QColor(103, 103, 103)


def p_minus():
    path = QPainterPath()
    path.moveTo(4, 8)
    path.lineTo(12, 8)
    return path


def dc_minus():
    return [QSize(16, 16), (p_minus(), "2", _listIconsStrokeColor)]


def dc_plus():
    path = p_minus()
    path.moveTo(8, 4)
    path.lineTo(8, 12)
    return [QSize(16, 16), (path, "2", _listIconsStrokeColor)]


def i_minus():
    icon = PathIcon(16, 16)
    path = p_minus()
    icon.addStrokePath(path, _listIconsStrokeColor, 2)
    return icon


def i_plus():
    icon = PathIcon(16, 16)
    path = p_minus()
    path.moveTo(8, 4)
    path.lineTo(8, 12)
    icon.addStrokePath(path, _listIconsStrokeColor, 2)
    return icon


def p_down():
    path = QPainterPath()
    path.moveTo(8, 4)
    path.lineTo(8, 12)
    path.moveTo(4, 8)
    path.lineTo(8, 12)
    path.lineTo(12, 8)
    return path


def dc_down():
    return [QSize(16, 16), (p_down(), "2a", _listIconsStrokeColor)]


def dc_up():
    path = p_down() * QTransform.fromScale(1, -1).translate(0, -16)
    return [QSize(16, 16), (path, "2a", _listIconsStrokeColor)]


def i_warning():
    icon = PathIcon(20, 20)
    path = QPainterPath()
    path.moveTo(4, 16)
    path.lineTo(16, 16)
    path.lineTo(10, 5)
    path.closeSubpath()
    path_ = QPainterPath()
    path_.addRect(9, 8, 2, 4)
    path_.addRect(9, 13, 2, 2)
    icon.addFillPath(path - path_, QColor(230, 20, 20), antialiasing=True)
    return icon


def p_ellipses():
    circ1 = QPainterPath()
    circ1.addEllipse(5, 1, 14, 14)
    circ2 = QPainterPath()
    circ2.addEllipse(1, 9, 10, 10)
    return circ1, circ2


def dc_invscale():
    circ1, circ2 = p_ellipses()
    path = circ1 - circ2
    path.addPath(circ2)
    return [
        QSize(20, 20),
        (circ2, "f", _sidebarIconsFillColor),
        (path, "1a", _sidebarIconsStrokeColor),
    ]


def dc_scale():
    circ1, circ2 = p_ellipses()
    path = circ2 - circ1
    path.addPath(circ1)
    return [
        QSize(20, 20),
        (circ1, "f", _sidebarIconsFillColor),
        (path, "1a", _sidebarIconsStrokeColor),
    ]


def p_rotate():
    path = QPainterPath()
    path.moveTo(18, 11)
    path.cubicTo(17, 15.5, 14, 18, 10, 18)
    path.cubicTo(5.5, 18, 2, 14.5, 2, 10)
    path.cubicTo(2, 6, 5.5, 2, 10, 2)
    path.cubicTo(14, 2, 17, 4, 17, 7)
    path.moveTo(18, 4)
    path.lineTo(18, 7)
    path.lineTo(15, 7)
    path.addRect(9, 9, 2, 2)
    return path


def dc_rotate():
    t = QTransform.fromScale(-1, 1).translate(-20, 0)
    return [QSize(20, 20), (p_rotate() * t, "1a", _sidebarIconsStrokeColor)]


def dc_invrotate():
    return [QSize(20, 20), (p_rotate(), "1a", _sidebarIconsStrokeColor)]


def p_skew():
    path1 = QPainterPath()
    path1.moveTo(11, 2)
    path1.lineTo(18, 2)
    path1.lineTo(10, 18)
    path1.lineTo(3, 18)
    path1.closeSubpath()
    path2 = QPainterPath(path1)
    path2.moveTo(8, 2)
    path2.lineTo(2, 2)
    path2.lineTo(2, 14)
    return path1, path2


def dc_invskew():
    path1, path2 = p_skew()
    t = QTransform.fromScale(-1, 1).translate(-20, 0)
    return [
        QSize(20, 20),
        (path1 * t, "f", _sidebarIconsFillColor),
        (path2 * t, "1", _sidebarIconsStrokeColor),
    ]


def dc_skew():
    path1, path2 = p_skew()
    return [
        QSize(20, 20),
        (path1, "f", _sidebarIconsFillColor),
        (path2, "1", _sidebarIconsStrokeColor),
    ]


def dc_snap():
    path = QPainterPath()
    path.addEllipse(8, 8, 5, 5)
    path_ = QPainterPath()
    path_.moveTo(10, 2)
    path_.lineTo(10, 18)
    path_.moveTo(2, 10)
    path_.lineTo(18, 10)
    return [
        QSize(20, 20),
        (path, "f", _sidebarIconsFillColor),
        (path_, "1", _sidebarIconsStrokeColor),
    ]


def p_cubes():
    notch = 5
    cube1 = QPainterPath()
    cube1.moveTo(2, 2)
    cube1.lineTo(18 - notch, 2)
    cube1.lineTo(18 - notch, 18 - notch)
    cube1.lineTo(2, 18 - notch)
    cube1.closeSubpath()
    cube2 = QPainterPath()
    cube2.moveTo(2 + notch, 2 + notch)
    cube2.lineTo(18, 2 + notch)
    cube2.lineTo(18, 18)
    cube2.lineTo(2 + notch, 18)
    cube2.closeSubpath()
    return cube1, cube2


def dc_union():
    cube1, cube2 = p_cubes()
    path = cube1 + cube2
    return [
        QSize(20, 20),
        (path, "f", _sidebarIconsFillColor),
        (path, "1", _sidebarIconsStrokeColor),
    ]


def dc_subtract():
    cube1, cube2 = p_cubes()
    path = cube1 - cube2
    path_ = cube2
    path_.addPath(path)
    return [
        QSize(20, 20),
        (path, "f", _sidebarIconsFillColor),
        (path_, "1", _sidebarIconsStrokeColor),
    ]


def dc_intersect():
    cube1, cube2 = p_cubes()
    intersect = cube1 & cube2
    cubes = cube1
    cubes.addPath(cube2)
    return [
        QSize(20, 20),
        (intersect, "f", _sidebarIconsFillColor),
        (cubes, "1", _sidebarIconsStrokeColor),
    ]


def dc_xor():
    cube1, cube2 = p_cubes()
    intersect = cube1 & cube2
    cubes = cube1
    cubes.addPath(cube2)
    return [
        QSize(20, 20),
        (cubes - intersect, "f", _sidebarIconsFillColor),
        (cubes, "1", _sidebarIconsStrokeColor),
    ]


def p_mirror():
    raise NotImplementedError


def dc_hmirror():
    path = QPainterPath()
    path.moveTo(8, 18)
    path.lineTo(1, 18)
    path.lineTo(8, 1)
    path.closeSubpath()
    path_ = QPainterPath(path)
    path_.moveTo(11, 18)
    path_.lineTo(19, 18)
    path_.lineTo(11, 1)
    path_.closeSubpath()
    return [
        QSize(20, 20),
        (path, "f", _sidebarIconsFillColor),
        (path_, "1", _sidebarIconsStrokeColor),
    ]


def dc_vmirror():
    path = QPainterPath()
    path.moveTo(2, 1)
    path.lineTo(19, 8)
    path.lineTo(2, 8)
    path.closeSubpath()
    path_ = QPainterPath(path)
    path_.moveTo(2, 11)
    path_.lineTo(19, 11)
    path_.lineTo(2, 19)
    path_.closeSubpath()
    return [
        QSize(20, 20),
        (path, "f", _sidebarIconsFillColor),
        (path_, "1", _sidebarIconsStrokeColor),
    ]


def dc_alignhleft():
    path = QPainterPath()
    path.moveTo(2, 2)
    path.lineTo(2, 18)
    path.lineTo(3, 18)
    path.lineTo(3, 2)
    path.closeSubpath()
    path.moveTo(3, 4)
    path.lineTo(13, 4)
    path.lineTo(13, 8)
    path.lineTo(3, 8)
    path.moveTo(3, 12)
    path.lineTo(18, 12)
    path.lineTo(18, 16)
    path.lineTo(3, 16)
    return [QSize(20, 20), (path, "1", _sidebarIconsStrokeColor)]


def dc_alignhcenter():
    path = QPainterPath()
    path.moveTo(9, 2)
    path.lineTo(9, 18)
    path.lineTo(10, 18)
    path.lineTo(10, 2)
    path.closeSubpath()
    path.moveTo(5, 4)
    path.lineTo(15, 4)
    path.lineTo(15, 8)
    path.lineTo(5, 8)
    path.closeSubpath()
    path.moveTo(2, 12)
    path.lineTo(18, 12)
    path.lineTo(18, 16)
    path.lineTo(2, 16)
    path.closeSubpath()
    return [QSize(20, 20), (path, "1", _sidebarIconsStrokeColor)]


def dc_alignhright():
    path = QPainterPath()
    path.moveTo(17, 2)
    path.lineTo(17, 18)
    path.lineTo(18, 18)
    path.lineTo(18, 2)
    path.closeSubpath()
    path.moveTo(17, 4)
    path.lineTo(8, 4)
    path.lineTo(8, 8)
    path.lineTo(17, 8)
    path.moveTo(17, 12)
    path.lineTo(2, 12)
    path.lineTo(2, 16)
    path.lineTo(17, 16)
    return [QSize(20, 20), (path, "1", _sidebarIconsStrokeColor)]


def dc_alignvtop():
    path = QPainterPath()
    path.moveTo(2, 2)
    path.lineTo(18, 2)
    path.lineTo(18, 3)
    path.lineTo(2, 3)
    path.closeSubpath()
    path.moveTo(4, 3)
    path.lineTo(4, 18)
    path.lineTo(8, 18)
    path.lineTo(8, 3)
    path.moveTo(12, 3)
    path.lineTo(12, 13)
    path.lineTo(16, 13)
    path.lineTo(16, 3)
    return [QSize(20, 20), (path, "1", _sidebarIconsStrokeColor)]


def dc_alignvcenter():
    path = QPainterPath()
    path.moveTo(2, 9)
    path.lineTo(18, 9)
    path.lineTo(18, 10)
    path.lineTo(2, 10)
    path.closeSubpath()
    path.moveTo(4, 2)
    path.lineTo(4, 18)
    path.lineTo(8, 18)
    path.lineTo(8, 2)
    path.closeSubpath()
    path.moveTo(12, 5)
    path.lineTo(12, 15)
    path.lineTo(16, 15)
    path.lineTo(16, 5)
    path.closeSubpath()
    return [QSize(20, 20), (path, "1", _sidebarIconsStrokeColor)]


def dc_alignvbottom():
    path = QPainterPath()
    path.moveTo(2, 17)
    path.lineTo(18, 17)
    path.lineTo(18, 18)
    path.lineTo(2, 18)
    path.closeSubpath()
    path.moveTo(4, 17)
    path.lineTo(4, 2)
    path.lineTo(8, 2)
    path.lineTo(8, 17)
    path.moveTo(12, 17)
    path.lineTo(12, 8)
    path.lineTo(16, 8)
    path.lineTo(16, 17)
    return [QSize(20, 20), (path, "1", _sidebarIconsStrokeColor)]
