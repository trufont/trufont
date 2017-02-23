"""
Icon db using PathIcon.
"""
from PyQt5.QtGui import QColor, QPainterPath, QTransform
from trufont.objects.pathIcon import PathIcon

__all__ = ["icon"]

_listIconsStrokeColor = QColor(90, 90, 90)
_sidebarIconsFillColor = QColor(187, 187, 187)
_sidebarIconsStrokeColor = QColor(103, 103, 103)


def p_minus():
    path = QPainterPath()
    path.moveTo(4, 8)
    path.lineTo(12, 8)
    return path


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


def i_down():
    icon = PathIcon(16, 16)
    path = p_down()
    icon.addStrokePath(path, _listIconsStrokeColor, 2, True)
    return icon


def i_up():
    icon = PathIcon(16, 16)
    path = p_down() * QTransform.fromScale(1, -1).translate(0, -16)
    icon.addStrokePath(path, _listIconsStrokeColor, 2, True)
    return icon


def p_ellipses():
    circ1 = QPainterPath()
    circ1.addEllipse(5, 1, 14, 14)
    circ2 = QPainterPath()
    circ2.addEllipse(1, 9, 10, 10)
    return circ1, circ2


def i_invscale():
    circ1, circ2 = p_ellipses()
    icon = PathIcon(20, 20)
    icon.addFillPath(circ2, _sidebarIconsFillColor)
    path_ = circ1 - circ2
    path_.addPath(circ2)
    icon.addStrokePath(path_, _sidebarIconsStrokeColor, antialiasing=True)
    return icon


def i_scale():
    circ1, circ2 = p_ellipses()
    icon = PathIcon(20, 20)
    icon.addFillPath(circ1, _sidebarIconsFillColor)
    path_ = circ2 - circ1
    path_.addPath(circ1)
    icon.addStrokePath(path_, _sidebarIconsStrokeColor, antialiasing=True)
    return icon


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


def i_rotate():
    icon = PathIcon(20, 20)
    path = p_rotate()
    t = QTransform.fromScale(-1, 1).translate(-20, 0)
    icon.addStrokePath(path * t, _sidebarIconsStrokeColor, antialiasing=True)
    return icon


def i_invrotate():
    icon = PathIcon(20, 20)
    path = p_rotate()
    icon.addStrokePath(path, _sidebarIconsStrokeColor, antialiasing=True)
    return icon


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


def i_invskew():
    icon = PathIcon(20, 20)
    path1, path2 = p_skew()
    t = QTransform.fromScale(-1, 1).translate(-20, 0)
    icon.addFillPath(path1 * t, _sidebarIconsFillColor)
    icon.addStrokePath(path2 * t, _sidebarIconsStrokeColor)
    return icon


def i_skew():
    icon = PathIcon(20, 20)
    path1, path2 = p_skew()
    icon.addFillPath(path1, _sidebarIconsFillColor)
    icon.addStrokePath(path2, _sidebarIconsStrokeColor)
    return icon


def i_snap():
    icon = PathIcon(20, 20)
    path = QPainterPath()
    path.moveTo(10, 2)
    path.lineTo(10, 18)
    path.moveTo(2, 10)
    path.lineTo(18, 10)
    icon.addStrokePath(path, _sidebarIconsStrokeColor)
    path = QPainterPath()
    path.addEllipse(8, 8, 5, 5)
    icon.addFillPath(path, _sidebarIconsFillColor)
    return icon


def p_cubes():
    notch = 5
    cube1 = QPainterPath()
    cube1.moveTo(2, 2)
    cube1.lineTo(18-notch, 2)
    cube1.lineTo(18-notch, 18-notch)
    cube1.lineTo(2, 18-notch)
    cube1.closeSubpath()
    cube2 = QPainterPath()
    cube2.moveTo(2+notch, 2+notch)
    cube2.lineTo(18, 2+notch)
    cube2.lineTo(18, 18)
    cube2.lineTo(2+notch, 18)
    cube2.closeSubpath()
    return cube1, cube2


def i_union():
    icon = PathIcon(20, 20)
    cube1, cube2 = p_cubes()
    path = cube1 + cube2
    icon.addFillPath(path, _sidebarIconsFillColor)
    icon.addStrokePath(path, _sidebarIconsStrokeColor)
    return icon


def i_subtract():
    icon = PathIcon(20, 20)
    cube1, cube2 = p_cubes()
    path = cube1 - cube2
    icon.addFillPath(path, _sidebarIconsFillColor)
    path_ = cube2
    path_.addPath(path)
    icon.addStrokePath(path_, _sidebarIconsStrokeColor)
    return icon


def i_intersect():
    icon = PathIcon(20, 20)
    cube1, cube2 = p_cubes()
    icon.addFillPath(cube1 & cube2, _sidebarIconsFillColor)
    cubes = cube1
    cubes.addPath(cube2)
    icon.addStrokePath(cubes, _sidebarIconsStrokeColor)
    return icon


def i_xor():
    icon = PathIcon(20, 20)
    cube1, cube2 = p_cubes()
    intersect = cube1 & cube2
    cubes = cube1
    cubes.addPath(cube2)
    icon.addFillPath(cubes - intersect, _sidebarIconsFillColor)
    icon.addStrokePath(cubes, _sidebarIconsStrokeColor)
    return icon


def p_mirror():
    raise NotImplementedError


def i_hmirror():
    icon = PathIcon(20, 20)
    path = QPainterPath()
    path.moveTo(8, 18)
    path.lineTo(1, 18)
    path.lineTo(8, 1)
    path.closeSubpath()
    icon.addFillPath(path, _sidebarIconsFillColor)
    path_ = QPainterPath(path)
    path_.moveTo(11, 18)
    path_.lineTo(19, 18)
    path_.lineTo(11, 1)
    path_.closeSubpath()
    icon.addStrokePath(path_, _sidebarIconsStrokeColor)
    return icon


def i_vmirror():
    icon = PathIcon(20, 20)
    path = QPainterPath()
    path.moveTo(2, 1)
    path.lineTo(19, 8)
    path.lineTo(2, 8)
    path.closeSubpath()
    icon.addFillPath(path, _sidebarIconsFillColor)
    path_ = QPainterPath(path)
    path_.moveTo(2, 11)
    path_.lineTo(19, 11)
    path_.lineTo(2, 19)
    path_.closeSubpath()
    icon.addStrokePath(path_, _sidebarIconsStrokeColor)
    return icon


def i_alignhleft():
    icon = PathIcon(20, 20)
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
    icon.addStrokePath(path, _sidebarIconsStrokeColor)
    return icon


def i_alignhcenter():
    icon = PathIcon(20, 20)
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
    icon.addStrokePath(path, _sidebarIconsStrokeColor)
    return icon


def i_alignhright():
    icon = PathIcon(20, 20)
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
    icon.addStrokePath(path, _sidebarIconsStrokeColor)
    return icon


def i_alignvtop():
    icon = PathIcon(20, 20)
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
    icon.addStrokePath(path, _sidebarIconsStrokeColor)
    return icon


def i_alignvcenter():
    icon = PathIcon(20, 20)
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
    icon.addStrokePath(path, _sidebarIconsStrokeColor)
    return icon


def i_alignvbottom():
    icon = PathIcon(20, 20)
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
    icon.addStrokePath(path, _sidebarIconsStrokeColor)
    return icon


def icon(key):
    return globals()[key]()


def iconPath(key):
    raise NotImplementedError
