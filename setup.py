#!/usr/bin/env python
from setuptools import setup

try:
    import fontTools  # noqa
except:
    print("*** Warning: trufont requires fontTools, see:")
    print("    https://github.com/behdad/fonttools/")

try:
    import ufoLib  # noqa
except:
    print("*** Warning: trufont requires ufoLib, see:")
    print("    https://github.com/unified-font-object/ufoLib")

try:
    import defcon  # noqa
except:
    print("*** Warning: trufont requires defcon (the python3-ufo3 branch), "
          "see:")
    print("    https://github.com/trufont/defcon")

setup(
    name="trufont",
    version="0.4.0",
    description="TruFont, a modular and cross-platform font editor.",
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="http://trufont.github.io",
    license="GNU LGPL v3/GNU GPL v3",
    packages=[
        "trufont",
        "trufont.controls",
        "trufont.drawingTools",
        "trufont.objects",
        "trufont.representationFactories",
        "trufont.resources",
        "trufont.tools",
        "trufont.windows",
    ],
    entry_points={
        "gui_scripts": [
            "trufont =  trufont.__main__:main"
        ]
    },
    package_dir={"": "Lib"},
    platforms=["Linux", "Win32", "Mac OS X"],
    classifiers=[
        "Environment :: GUI",
        "Programming Language :: Python :: 3.4",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Fonts",
    ],
    test_suite="tests",
)
