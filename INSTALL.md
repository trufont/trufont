# Mac OS X

## Dependencies

### Python 3

Learn more: https://docs.python.org/3

Install with [homebrew](http://brew.sh),

    sudo xcodebuild -license ;
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" ;
    brew install python3 ;

### PyQt5

Learn more: https://www.riverbankcomputing.com/software/pyqt

Install with homebrew,

    brew install pyqt5 ;

### Python dependencies

    sudo pip install -r requirements.txt

## Trufont

Homepage: https://trufont.github.io

To install and run,

    cd .. ;
    git clone --depth=1 https://github.com/trufont/trufont ;
    cd trufont ;
    sudo python3 setup.py install --record installed-files.txt ;
    python3 -m trufont ;

Or to then run from source,

    cd Lib/ ; 
    python3 -m trufont ;

To build installation packages,

    cd Lib/ ;
    sh build.sh ;

Distribution packages will be placed in in `Lib/dist/`.
To build an installation package for Mac OS X 10.9, you must build the package on that version of the OS.

## Uninstall

Files are installed into `/usr/local/lib/python3.5/site-packages/` 

    sudo easy_install pip ;
    sudo pip uninstall -r requirements.txt

If you installed TruFont with `setup.py`, it can be uninstalled with this command
(be careful with rm!):

    cat installed-files.txt | xargs sudo rm --verbose -vr

# Debian, Ubuntu

(Note that we are using Python 3.4)

## Dependencies

    sudo apt-get install -qq -y python3-pyqt5 python3-pyqt5.qtsvg python3-flake8 ;
    sudo pip3 install -r requirements.txt

## Trufont

To install and run,

    cd .. ;
    git clone --depth=1 https://github.com/trufont/trufont ;
    cd trufront ;
    sudo python3 setup.py install --record installed-files.txt ;
    python3 -m trufont ;

Or to then run from source,

    cd Lib/ ; 
    python3 -m trufont ;

## Uninstall

Files are installed into `/usr/local/lib/python3.4/dist-packages/`

These can be removed with pip:

    sudo apt-get install python3-pip ;
    sudo pip3 uninstall -r requirements.txt

If you installed TruFont with `setup.py`, it can be uninstalled with this command
(be careful with rm!):

    cat installed-files.txt | xargs sudo rm --verbose -vr

# Virtualenv

[Virtualenv](https://virtualenv.pypa.io) is optional. If you plan to use it and you've installed
PyQt5 with Homebrew or Apt, then add the `--system-site-packages` flag when creating the Virtualenv
to make PyQt5 available:

    virtualenv --system-site-packages virutalenv-name
