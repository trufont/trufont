# TruFont [![Build Status](https://travis-ci.org/trufont/trufont.svg)](https://travis-ci.org/trufont/trufont)

![fontView Window](misc/fontView.png)

TruFont is a font-editing application written with Python3, ufoLib, defcon and
PyQt5.

## Getting started

1. Install Python 3 
    - OS X: Install using [Homebrew]: `brew install python3 && brew linkapps python3`
    - Windows: Download installer from https://www.python.org/downloads/
    - Linux: It's usually packaged with the OS.

2. Install PyQt5:
    - OS X: `brew install pyqt5`
    - Windows: You can download the binary installers (32 or 64 bit) from:
        https://riverbankcomputing.com/software/pyqt/download5
    - Linux: Follow instructions to compile PyQt5 (and SIP) from source:
        http://pyqt.sourceforge.net/Docs/PyQt5/installation.html

3. Set up a new Python virtual environment using `virtualenv`.
    - Install or update the virtualenv module with `pip3 install --upgrade virtualenv`.
       You may require `sudo` access on Linux. Alternatively, you can install it in
       the Python user directory: `pip3 install --user --upgrade virtualenv`.
    - Create a new virtual environment, and give it access to the system
        site-packages to make sure PyQt5 can be imported:
        `python3 -m virtualenv --system-site-packages trufont`
    - Activate the newly created environment:
        - OS X or Linux: `source trufont/bin/activate`
        - Windows: `trufont\Scripts\activate.bat`
    - Run `deactivate` when you wish to exit the virtual environment.

4. Install dependencies: `pip3 install -r requirements.txt`

5. Install TruFont: `pip3 install .`
    Or if you wish to edit the source code, install in "editable" mode:
    `pip3 install -e .` 

6. Run the app as `trufont`.

## Dependencies

- Python 3
- PyQt5
- [fontTools]
- [ufoLib]
- [defcon, python3-ufo3 branch]
- cython & [booleanOperations]

Optional:

- [extractor, python3-ufo3 branch]
- [ufo2fdk, python3-ufo3 branch]

[fontTools]: https://github.com/behdad/fonttools
[ufoLib]: https://github.com/unified-font-object/ufoLib
[defcon, python3-ufo3 branch]: https://github.com/trufont/defcon
[booleanOperations]: https://github.com/trufont/booleanOperations
[extractor, python3-ufo3 branch]: https://github.com/trufont/extractor
[ufo2fdk, python3-ufo3 branch]: https://github.com/trufont/ufo2fdk
[Homebrew]: http://brew.sh/
