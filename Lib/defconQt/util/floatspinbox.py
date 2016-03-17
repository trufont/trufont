from PyQt5.QtCore import QLocale
from PyQt5.QtWidgets import QDoubleSpinBox


# Hides decimals unless used but shows decimal point to hint at the type of
# box.  No more "250,00000000", just "250,".
class FloatSpinBox(QDoubleSpinBox):
    def textFromValue(self, value):
        decimalPoint = QLocale().decimalPoint()
        if value - int(value) == 0:  # if is int
            return "{0}{1}".format(str(int(value)), decimalPoint)
        else:
            return str(value).replace(".", decimalPoint)
