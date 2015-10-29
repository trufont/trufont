# Mac OS X

## Dependencies

### Python 3

Learn more: https://docs.python.org/3

Install with [homebrew](http://brew.sh),

    sudo xcodebuild -license ;
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" ;
    brew install python3 ;
	brew linkapps python3 ;

Note: You can have multiple versions of Python on your system, and you just need to use a version prefix (e.g. `python3` or `python3.4` or `python3.5`) to ensure you are using Python 3. 

### PyQt5

Learn more: https://www.riverbankcomputing.com/software/pyqt

Install with homebrew,

    brew install pyqt5 ;

### fontTools

Learn more: https://github.com/behdad/fonttools

    git clone --depth=1 https://github.com/behdad/fonttools ;
    cd fonttools/ ;
    sudo python3 setup.py install --record installed-files.txt ;

### RoboFab

Learn more: http://www.robofab.com

In particular, https://github.com/trufont/robofab/tree/python3-ufo3

    cd .. ;
    git clone --depth=1 --branch=python3-ufo3 https://github.com/trufont/robofab ;
    cd robofab ;
    sudo python3 setup.py install --record installed-files.txt ;

### defcon

Homepage: https://readthedocs.org/projects/ts-defcon

In particular, https://github.com/trufont/defcon/tree/python3-ufo3

    cd .. ;
    git clone --depth=1 --branch=python3-ufo3 https://github.com/trufont/defcon ;
    cd robofab ;
    sudo python3 setup.py install --record installed-files.txt ;

### PyInstaller

Homepage: http://www.pyinstaller.org

    sudo pip install PyInstaller ;

## Trufont

Homepage: https://trufont.github.io

To install and run,

    cd .. ;
    git clone --depth=1 https://github.com/trufont/trufont ;
    cd trufont ;
    sudo python3 setup.py install --record installed-files.txt ;
    python3 -m defconQt ;

Or to then run from source,

    cd Lib/ ; 
    python3 -m defconQt ;

To build installation packages,

    cd Lib/ ;
    sh build.sh ;

Distribution packages will be placed in in `Lib/dist/`.
To build an installation package for Mac OS X 10.9, you must build the package on that version of the OS.

## Uninstall

Files are installed into `/usr/local/lib/python3.5/site-packages/` 

    sudo easy_install pip ;
    sudo pip uninstall robofab defcon defconQt ;

To get rid of all remaining files (be careful with rm!) for each package installed above,

    cat installed-files.txt | xargs sudo rm --verbose -vr

# Debian, Ubuntu

(Note that we are using Python 3.4)

## Dependencies

    sudo apt-get install -qq -y python3-pyqt5 python3-pyqt5.qtsvg python3-flake8 ;
    git clone --depth=1 --branch=python3-ufo3 https://github.com/trufont/defcon ;
    git clone --depth=1 --branch=python3-ufo3 https://github.com/trufont/robofab ;
    git clone --depth=1 --branch=python3-ufo3 https://github.com/trufont/ufo2fdk ;
    git clone --depth=1 https://github.com/behdad/fonttools.git ;

    cd defcon ;
    sudo python3.4 setup.py install --record installed-files.txt ;

    cd ../robofab ;
    sudo python3.4 setup.py install --record installed-files.txt ;

    cd ../ufo2fdk ;
    sudo python3.4 setup.py install --record installed-files.txt ;

    cd ../fonttools ;
    sudo python3.4 setup.py install --record installed-files.txt ;

## TruFont

To install and run,

    cd .. ;
    git clone --depth=1 https://github.com/trufont/trufont ;
    cd trufront ;
    sudo python3 setup.py install --record installed-files.txt ;
    python3 -m defconQt ;

Or to then run from source,

    cd Lib/ ; 
    python3 -m defconQt ;

## Uninstall

Files are installed into `/usr/local/lib/python3.4/dist-packages/`

These can be partially removed with pip,

    sudo apt-get install python3-pip ;
    sudo pip3 uninstall robofab defcon ufo2fdk ufoLib defconQt ;

To get rid of all remaining files (be careful with rm!) for each package installed above,

    cat installed-files.txt | xargs sudo rm --verbose -vr
