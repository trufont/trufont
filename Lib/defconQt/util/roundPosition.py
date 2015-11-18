def roundPosition(value):
    value = value * 10  # self._scale
    value = round(value) - .5
    value = value * .1  # self._inverseScale
    return value
