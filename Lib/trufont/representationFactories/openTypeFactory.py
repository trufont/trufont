from ufo2ft import compileOTF, compileTTF


def TTFontFactory(font):
    otf = compileOTF(font)
    return otf


def QuadraticTTFontFactory(font):
    ttf = compileTTF(font)
    return ttf
