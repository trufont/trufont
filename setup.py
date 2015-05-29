#!/usr/bin/env python

import sys
from distutils.core import setup

try:
    import fontTools
except:
    print "*** Warning: defcon requires FontTools, see:"
    print "    fonttools.sf.net"

try:
    import robofab
except:
    print "*** Warning: defcon requires RoboFab, see:"
    print "    robofab.com"

#if "sdist" in sys.argv:
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



setup(name="defconQt",
    version="0.1",
    description="A set of Qt interface objects for working with font data.",
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
#    url="",
    license="GNU LGPL 2.1/GNU GPL v3",
    # TODO: populate
    packages=["defconQt"],
    package_dir={"":"Lib"}
)