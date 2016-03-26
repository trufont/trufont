#!/usr/bin/env python
# import sys
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
    version="0.3.0",
    description="TruFont, a cross-platform font editor. Includes a set of Qt "
                "objects for working with font data.",
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="http://trufont.github.io",
    license="GNU LGPL v3/GNU GPL v3",
    packages=[
        "trufont",
        "trufont.objects",
        "trufont.representationFactories",
        "trufont.tools",
        "trufont.util",
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
