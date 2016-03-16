#!/usr/bin/env python

from glob import glob
import os
from setuptools import setup
import shutil
from subprocess import call
import sys

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


name = 'TruFont'
app = []
options = {}
data_files = []
setup_requires = []
build_for_mac = sys.platform == 'darwin' and sys.argv[1] == 'py2app'

if build_for_mac:
    options['py2app'] = {
        'argv_emulation': True,
        'iconfile': 'Lib/defconQt/resources/app.icns',
        'includes': ['sip', 'PyQt5', 'defconQt'],
        'frameworks': [
            glob('/usr/local/Cellar/qt5*/5.*/plugins/platforms/libqcocoa.dylib')[0],
            glob('/usr/local/Cellar/qt5*/5.*/plugins/iconengines/libqsvgicon.dylib')[0],
        ],
        'qt_plugins': ['*'],
        'plist': {
            'CFBundleIdentifier': 'io.github.trufont',
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeExtensions': [
                        'ufo',
                    ],
                    'CFBundleTypeName': 'Unified Font Object',
                    'CFBundleTypeRole': 'Editor',
                    'LSTypeIsPackage': True,
                }
            ],
            'NSHighResolutionCapable': 'True',
            'NSHumanReadableCopyright': '',
        }
    }

    app.append('Lib/defconQt/__main__.py')
    data_files.append('qt.conf')
    setup_requires.append('py2app')


setup(
    name=name,
    version="0.3.0",
    description="TruFont, a cross-platform font editor. Includes a set of Qt "
                "objects for working with font data.",
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="http://trufont.github.io",
    license="GNU LGPL v3/GNU GPL v3",
    packages=[
        "defconQt",
        "defconQt.objects",
        "defconQt.representationFactories",
        "defconQt.tools",
        "defconQt.util",
    ],
    entry_points={
        "gui_scripts": [
            "trufont =  defconQt.__main__:main"
        ]
    },
    package_dir={"": "Lib"},
    app=app,
    data_files=data_files,
    options=options,
    setup_requires=setup_requires,
    platforms=["Linux", "Win32", "Mac OS X"],
    classifiers=[
        "Environment :: GUI",
        "Programming Language :: Python :: 3.4",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Fonts",
    ],
    test_suite="tests",
)


if build_for_mac:
    # Copy dylibs to Qt PlugIns directory
    os.makedirs(
        'dist/' + name + '.app/Contents/PlugIns/platforms',
        exist_ok=True
    )
    os.makedirs(
        'dist/' + name + '.app/Contents/PlugIns/iconengines',
        exist_ok=True
    )
    shutil.copyfile(
        'dist/' + name + '.app/Contents/Frameworks/libqcocoa.dylib',
        'dist/' + name + '.app/Contents/PlugIns/platforms/libqcocoa.dylib'
    )
    shutil.copyfile(
        'dist/' + name + '.app/Contents/Frameworks/libqsvgicon.dylib',
        'dist/' + name + '.app/Contents/PlugIns/iconengines/libqsvgicon.dylib'
    )
