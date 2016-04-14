from husl import husl_to_rgb
from PyQt5.QtGui import QColor
import random

# http://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/  # noqa
golden_ratio_conjugate = 0.618033988749895


class ColorGenerator:
    """
    A static-state random color generator that uses the `HUSL color space`_.

    .. _`HUSL color space`: http://www.husl-colors.org
    """
    seed = random.random()
    # http://www.husl-colors.org/syntax/
    minS = random.uniform(30, 70)
    maxS = minS + 30
    minL = random.uniform(50, 70)
    maxL = minL + 20

    @classmethod
    def getColor(cls):
        cls.seed = (cls.seed + golden_ratio_conjugate) % 1
        hue = 360 * cls.seed
        sat = random.uniform(cls.minS, cls.maxS)
        lum = random.uniform(cls.minL, cls.maxL)
        return husl_to_rgb(hue, sat, lum)

    @classmethod
    def getQColor(cls):
        color = cls.getColor()
        return QColor.fromRgbF(*color)

    @classmethod
    def setSaturationFromRange(cls, lo, hi):
        rg = hi - lo
        cls.minS = random.uniform(lo, hi)
        cls.maxS = cls.minS + round(min(3*rg/4, 100-hi))

    @classmethod
    def setLightnessFromRange(cls, lo, hi):
        rg = hi - lo
        cls.minL = random.uniform(lo, hi)
        cls.maxL = cls.minL + round(min(3*rg/4, 100-hi))
