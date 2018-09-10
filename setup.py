#!/usr/bin/env python
from setuptools import setup, find_packages


with open('README.rst', 'r', encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="trufont",
    version="1.0.0.dev0",
    description="TruFont is a streamlined and hackable font editor.",
    long_description=long_description,
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="http://trufont.github.io",
    license="MPL 2.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    entry_points={
        "gui_scripts": [
            "trufont =  trufont.__main__:main"
        ]
    },
    install_requires=[
        "tfont>=0.1.0",
        "uharfbuzz>=0.2.0",
        "fonttools>=3.9.1",
        "skia-pathops>=0.1.4",
        "wxPython>=4.0.3",
    ],
    platforms=["Win32", "Mac OS X", "Linux"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Text Processing :: Fonts",
        "Topic :: Multimedia :: Graphics :: Editors :: Vector-Based",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    ],
    # test_suite="tests",
)
