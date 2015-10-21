#!/usr/bin/env python
# import sys
from distutils.core import setup

try:
    import fontTools  # noqa
except:
    print("*** Warning: trufont requires FontTools, see:")
    print("    https://github.com/behdad/fonttools/")

try:
    import robofab  # noqa
except:
    print("*** Warning: trufont requires RoboFab, see:")
    print("    https://github.com/trufont/robofab")

try:
    import defcon #noqa
except:
    print("*** Warning: trufont requires defcon, see:")
    print("    https://github.com/trufont/defcon")

# if "sdist" in sys.argv:
#    import os
#    import subprocess
#    import shutil
#    docFolder = os.path.join(os.getcwd(), "documentation")
#    # remove existing
#    doctrees = os.path.join(docFolder, "build", "doctrees")
#    if os.path.exists(doctrees):
#        shutil.rmtree(doctrees)
#    # compile
#    p = subprocess.Popen(["make", "html"], cwd=docFolder)
#    p.wait()
#    # remove doctrees
#    shutil.rmtree(doctrees)


setup(
    name="defconQt",
    version="0.1.0",
    description="Trufont, a cross-platform font editor (a set of Qt interface objects for working with font data).",
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="http://trufont.github.io",
    license="GNU LGPL 2.1/GNU GPL v3",
    packages=[
        "defconQt",
        "defconQt.objects",
        "defconQt.pens",
        "defconQt.representationFactories",
        "defconQt.util",
    ],
    scripts=["trufont"],
    package_dir={"": "Lib"},
    platforms=["Linux","Win32","Mac OS X"],
    classifiers=[
    "Environment :: GUI",
    "Programming Language :: Python :: 3.4",
    "Intended Audience :: Developers",
    "Topic :: Text Processing :: Fonts",
    ],
)
