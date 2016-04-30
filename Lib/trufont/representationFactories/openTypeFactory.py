from ufo2ft import compileOTF, compileTTF


def TTFontFactory(font, useProductionNames=False, optimizeCff=False):
    otf = compileOTF(
        font, useProductionNames=useProductionNames, optimizeCff=optimizeCff)
    return otf


def QuadraticTTFontFactory(font, useProductionNames=False):
    ttf = compileTTF(font, useProductionNames=useProductionNames)
    return ttf
