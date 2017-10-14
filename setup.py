#!/usr/bin/env python
from setuptools import setup, find_packages


with open('README.rst', 'r', encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="trufont",
    version="0.6.0.dev0",
    description="TruFont, a modular and cross-platform font editor.",
    long_description=long_description,
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="http://trufont.github.io",
    license="GNU LGPL v3/GNU GPL v3",
    package_dir={"": "Lib"},
    packages=find_packages("Lib"),
    entry_points={
        "gui_scripts": [
            "trufont =  trufont.__main__:main"
        ]
    },
    install_requires=[
        "pyqt5>=5.5.0",
        "fonttools>=3.17.0",
        "ufoLib>=2.1.0",
        "defcon>=0.3.4",
        "defconQt>=0.5.3",
        "ufo-extractor>=0.2.0",
        "ufo2ft>=0.5.3",
        "booleanOperations>=0.7.0",
        "hsluv>=0.0.2",
        "brotli>=0.5.2",
    ],
    platforms=["Linux", "Win32", "Mac OS X"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.5",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Fonts",
        'Topic :: Multimedia :: Graphics :: Editors :: Vector-Based',
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ],
    test_suite="tests",
)
