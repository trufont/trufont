# TruFont [![Build Status](https://travis-ci.org/trufont/trufont.svg)](https://travis-ci.org/trufont/trufont)

![fontView Window](misc/fontView.png)

[TruFont] is a font-editing application written with Python3, ufoLib, defcon and
PyQt5.

## Getting started

1. Install Python 3 
    - OS X: Install using [Homebrew]: `brew install python3 && brew linkapps python3`
    - Windows: Download installer from https://www.python.org/downloads/
    - Linux: It's usually packaged with the OS.

2. Set up a new Python virtual environment using `virtualenv`.
    - Install or update the virtualenv module with `pip3 install --upgrade virtualenv`.
       You may require `sudo` access on Linux. Alternatively, you can install it in
       the Python user directory: `pip3 install --user --upgrade virtualenv`.
    - Create a new virtual environment, here called '.venv':
        + OSX and Windows: `python3 -m virtualenv .venv`
        + Linux: You need to give the virtualenv access to the system's
        site-packages folder to make sure PyQt5 can be imported:
            `python3 -m virtualenv --system-site-packages .venv`
    - Activate the newly created environment:
        - OS X or Linux: `source .venv/bin/activate`
        - Windows: `.venv\Scripts\activate.bat`
    - Run `deactivate` when you wish to exit the virtual environment.

3. Install PyQt5 (version 5.5.0 or greater):
    - OS X and Windows: `pip install pyqt5`
    - Linux: Follow instructions to compile PyQt5 (and SIP) from source:
        http://pyqt.sourceforge.net/Docs/PyQt5/installation.html

4. Install other dependencies: `pip3 install -r requirements.txt`

5. Install TruFont: `pip3 install .`
    Or if you wish to edit the source code, install in "editable" mode:
    `pip3 install -e .` 

6. Run the app as `trufont`.

[Homebrew]: http://brew.sh/
[TruFont]: https://trufont.github.io
