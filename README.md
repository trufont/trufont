# TruFont [![Build Status](https://travis-ci.org/trufont/trufont.svg)](https://travis-ci.org/trufont/trufont)

![fontView Window](misc/fontView.png)

TruFont is a font-editing application written with Python3, ufoLib, defcon and
PyQt5.

## Getting started

1. Install dependencies with `pip install -r requirements.txt`

2. Install using `python setup.py install && trufont` or run under virtualenv:
   `cd Lib && python -m defconQt`

## Dependencies

Dependencies can be fetched with `pip install -r requirements.txt`

- Python 3
- PyQt5
- cython & [booleanOperations]
- [fontTools]
- [ufoLib]
- [defcon, python3-ufo3 branch]

Optional:

- [extractor, python3-ufo3 branch]
- [ufo2fdk, python3-ufo3 branch]

## Install notes

- On OSX, it is highly recommended to install all dependencies with [Homebrew]
  in order to have a correct Qt namespace (`brew` handles it all by itself).  
  Finish with `brew linkapps python3` to be able to call `python3` from the
  Terminal.
- You can have multiple versions of Python on your system, then you just need to
  use a version prefix, e.g.:
  * `python3`
  * `python3.4`
  * `python3.5`
  * …

[booleanOperations]: https://github.com/typemytype/booleanOperations
[fontTools]: https://github.com/behdad/fonttools
[ufoLib]: https://github.com/unified-font-object/ufoLib
[defcon, python3-ufo3 branch]: https://github.com/trufont/defcon
[extractor, python3-ufo3 branch]: https://github.com/trufont/extractor
[ufo2fdk, python3-ufo3 branch]: https://github.com/trufont/ufo2fdk
[Homebrew]: http://brew.sh/
