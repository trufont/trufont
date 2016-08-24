from collections.abc import Sequence
from PyQt5.QtGui import QImageReader, QPixmap
from PyQt5.QtWidgets import QApplication
from ufoLib import _getPlist, UFOLibError, writePlistAtomically
import os
import re
import runpy
import shutil
import stat
import traceback

LIB_PATH = "lib"
INFO_FILENAME = "info.plist"
RESOURCES_PATH = "resources"

_infoProperties = {
    "name": "The name of the extension.",
    "developer": "The name of the extension developer.",
    "developerURL": "The URL of the extension developer.",
    "addToMenu": "a dict of *path*, *name*, *shortcut*",
    "launchAtStartup": "Whether *mainScript* should be launched at startup.",
    "mainScript": "The extension entry-point Python file.",
    "tfVersionMajor": "The minimum required TruFont major version number.",
    "tfVersionMinor": "The minimum required TruFont minor version number.",
    "tfVersionPatch": "The minimum required TruFont patch version number.",
    "versionMajor": "The extension major version number.",
    "versionMinor": "The extension minor version number.",
    "versionPatch": "The extension major version number.",
}

_privateAttrsRe = re.compile(
    "^[A-Za-z]{2,6}((?!-)\\.[A-Za-z0-9-]{1,63}(?<!-))+$")


def init_info_property(cls, name, doc):
    setterName = '_set_{0}'.format(name)
    getterName = '_get_{0}'.format(name)

    def getter(self):
        return self._info.get(name, None)
    getter.__name__ = getterName

    def setter(self, value):
        self._info[name] = value
        if value is None:
            del self._info[name]
    setter.__name__ = setterName

    prop = property(getter, setter, doc)

    setattr(cls, setterName, setter)
    setattr(cls, getterName, getter)
    setattr(cls, name, prop)


def init_info_properties(cls):
    for name, setup in _infoProperties.items():
        init_info_property(cls, name, setup)
    return cls


def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)


@init_info_properties
class TExtension(object):

    def __init__(self, path=None):
        self._info = TExtensionInfo()
        self._path = path
        self._libPath = None
        self._resourcesPath = None

        if path:
            loader = TExtensionReader(self._path)
            loader.readInfo(self._info)

    def __repr__(self):
        path = self._path
        if path is not None and path.rstrip("\\/ ").endswith(".tfExt"):
            fileName = os.path.basename(path)[1]
            return "<%s>" % fileName
        return super().__repr__()

    # info and special-cased getters

    @property
    def info(self):
        return self._info

    def _get_tfVersion(self):
        if self.tfVersionMajor is None:
            return None
        return Version(
            (self.tfVersionMajor, self.tfVersionMinor, self.tfVersionPatch))

    def _set_tfVersion(self, value):
        if value is not None:
            value = Version(value)
        else:
            value = (None, None, None)
        self.tfVersionMajor, self.tfVersionMinor, self.tfVersionPatch = value

    tfVersion = property(
        _get_tfVersion, _set_tfVersion,
        doc="The minimum required TruFont version number.")

    def _get_version(self):
        if self.versionMajor is None:
            return None
        return Version(
            (self.versionMajor, self.versionMinor, self.versionPatch))

    def _set_version(self, value):
        if value is not None:
            value = Version(value)
        else:
            value = (None, None, None)
        self.versionMajor, self.versionMinor, self.versionPatch = value

    version = property(
        _get_version, _set_version, doc="The extension version number.")

    # settings and methods

    @property
    def path(self):
        return self._path

    @property
    def libPath(self):
        return self._libPath

    @libPath.setter
    def libPath(self, path):
        if path is not None:
            assert os.path.isdir(path)
        self._libPath = path

    @property
    def resourcesPath(self):
        return self._resourcesPath

    @resourcesPath.setter
    def resourcesPath(self, path):
        if path is not None:
            assert os.path.isdir(path)
        self._resourcesPath = path

    def save(self, path=None):
        # fetch path
        if path is None or path == self._path:
            return
        # write
        writer = TExtensionWriter(path)
        libPath = self._libPath
        if libPath is None and self._path is not None:
            libPath = os.path.join(self._path, LIB_PATH)
        writer.writeLib(libPath)
        writer.writeInfo(self._info)
        writer.writeResources(
            os.path.join(self._path, self._resourcesPath or RESOURCES_PATH))
        # done
        self._path = path

    def get(self, name, ext='*'):
        for file in os.listdir(self._path):
            if ext == '*' or file.endswith(ext):
                imageReader = QImageReader(file)
                if imageReader:
                    return QPixmap.fromImageReader(imageReader)
                return os.path.join(self._path, file)
        return None

    def install(self):
        app = QApplication.instance()
        if self._path is not None:
            fileName = os.path.basename(self._path)
        else:
            fileName = self.name or "Extension" + ".tfExt"
        folder = os.path.join(
            app.getExtensionsDirectory(), fileName)
        self.save(folder)
        app.registerExtension(self)

    def uninstall(self):
        app = QApplication.instance()
        folder = app.getScriptsDirectory()
        path = self._path
        if path.contains(folder):
            shutil.rmtree(path, onerror=remove_readonly)
            app.unregisterExtension(self)

    def validate(self):
        # TODO: should it e.g. look if the mainScript is an actual Python file
        raise NotImplementedError

    def run(self, subpath=None):
        libPath = self._libPath
        if libPath is None:
            libPath = LIB_PATH
        if subpath is None:
            subPath = self.mainScript
            if subPath is None:
                subPath = ""
        runPath = os.path.join(self._path, libPath, subpath)
        app = QApplication.instance()
        global_vars = app.globals()
        try:
            runpy.run_path(runPath, global_vars, self.name)
        except:
            traceback.print_exc()


class TExtensionInfo(dict):

    def __setitem__(self, key, value):
        if key not in _infoProperties.keys():
            if not _privateAttrsRe.match(key):
                raise AttributeError(
                    "Custom keys can only be added as reverse-domain names.")
        super().__setitem__(key, value)


class TExtensionReader(object):

    def __init__(self, path):
        if not os.path.exists(path):
            raise UFOLibError("The specified extension doesn't exist.")
        self._path = path

    _getPlist = _getPlist

    def _readInfo(self):
        data = self._getPlist(INFO_FILENAME, {})
        if not isinstance(data, dict):
            raise UFOLibError("info.plist is not properly formatted.")
        return data

    def readInfo(self, info):
        infoDict = self._readInfo()
        infoDataToSet = {}
        # standard attrs
        for attr in _infoProperties.keys():
            if attr in infoDict:
                value = infoDict[attr]
                del infoDict[attr]
            else:
                value = None
            if value is None:
                continue
            infoDataToSet[attr] = value
        # remaining private attrs
        for attr in infoDict:
            if not _privateAttrsRe.match(attr):
                continue
            value = infoDict[attr]
            if value is None:
                continue
            infoDataToSet[attr] = value
        for attr, value in infoDataToSet.items():
            try:
                info[attr] = value
            except AttributeError:
                raise UFOLibError(
                    "The supplied info object does not support setting a "
                    "necessary attribute (%s)." % attr)


class TExtensionWriter(object):

    def __init__(self, path):
        self._path = path
        self._makeDirectory()

    def _writePlist(self, fileName, data):
        """
        Write a property list. The errors that
        could be raised during the writing of
        a plist are unpredictable and/or too
        large to list, so, a blind try: except:
        is done. If an exception occurs, a
        UFOLibError will be raised.
        """
        self._makeDirectory()
        path = os.path.join(self._path, fileName)
        try:
            data = writePlistAtomically(data, path)
        except:
            raise UFOLibError(
                "The data for the file %s could not be written because it is "
                "not properly formatted." % fileName)

    def _makeDirectory(self, subDirectory=None):
        path = self._path
        if subDirectory:
            path = os.path.join(self._path, subDirectory)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def writeLib(self, origPath):
        if origPath is None:
            return
        canonicalPath = os.path.join(self._path, LIB_PATH)
        # cleanup existing script dir
        if os.path.exists(canonicalPath):
            try:
                shutil.rmtree(canonicalPath, onerror=remove_readonly)
            except:
                raise UFOLibError("Couldn't delete existing script folder.")
        # move in
        try:
            shutil.copytree(origPath, canonicalPath)
        except:
            raise UFOLibError(
                "Couldn't copy script files to the script folder.")

    def writeInfo(self, info):
        infoData = {}
        for key in info:
            if key in _infoProperties or _privateAttrsRe.match(key):
                value = info.get(key, None)
                if value is None:
                    continue
                infoData[key] = value
        # TODO: validate data here?
        # write file
        self._writePlist(INFO_FILENAME, infoData)

    def writeResources(self, origPath):
        pass


class Version(str):

    def __new__(self, value):
        # convert from sequence
        if isinstance(value, Sequence):
            assert len(value) == 3
            value = ".".join(str(num) for num in value)
        return super().__new__(Version, value)

    def __iter__(self):
        return iter(_stringToSequence(self))

    def _get_major(self):
        return _stringToSequence(self)[0]

    major = property(_get_major, "The major component.")

    def _get_minor(self):
        return _stringToSequence(self)[1]

    minor = property(_get_minor, "The minor component.")

    def _get_patch(self):
        return _stringToSequence(self)[2]

    patch = property(_get_patch, "The patch component.")


def _stringToSequence(value):
    major, minor, patch = [i.strip() for i in value.split(".")]
    value = []
    for component in (major, minor, patch):
        v = int(component)
        value.append(v)
    return value
