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
- [defcon]

Optional:

- [extractor]
- [ufo2fdk]

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
[defcon]: https://github.com/robotools/defcon
[extractor]: https://github.com/robotools/extractor
[ufo2fdk]: https://github.com/robotools/ufo2fdk
[Homebrew]: http://brew.sh/
