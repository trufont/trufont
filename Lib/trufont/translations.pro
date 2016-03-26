# This file collects 
# 1. All files with code that should be scanned for user-visible text.
# 2. All target languages and where to put those translations.
#
# Usage:
#   1. In the source, when inside a class derived from QObject that preferably
#      is not to be derived from or mixed with others[1], use `self.tr("Some
#      user visible text")` instead of the bare string to mark it for
#      translation. When outside a QObject-derived class (e.g. a stand-alone
#      function), use `QApplication.translate('context, e.g. stand-alone
#      function', "Some user visible text")`.
#   2. Add the file here unless already present.
#   3. Run `pylupdate5 translations.pro`. This will scan all (Python) source 
#      files and update the translation files if necessary. Previous
#      translations will stay, new and changed strings will be marked. The
#      generated .ts files are for translators to work on in Qt Linguist[2].
#   4. Once translators have forked over their translations, run 
#      `lrelease translations.pro` (exact lrelease name might vary). This
#      compiles .ts files into .qm files that are then loaded by application
#      code.
#
# [1]: http://pyqt.sourceforge.net/Docs/PyQt5/i18n.html#differences-between-pyqt5-and-qt
# [2]: https://doc.qt.io/qt-5/linguist-translators.html

CODECFORTR = UTF-8
CODECFORSRC = UTF-8

SOURCES += __main__.py \
           glyphCollectionView.py \
           featureTextEditor.py \
           fontInfo.py \
           fontView.py \
           glyphView.py \
           groupsView.py \
           metricsWindow.py \
           scriptingWindow.py \
           objects/glyphDialogs.py \
           tools/baseButton.py \
           tools/baseTool.py \
           tools/knifeTool.py \
           tools/penTool.py \
           tools/removeOverlapButton.py \
           tools/rulerTool.py \
           tools/selectionTool.py \
           util/drawing.py \
           util/glyphList.py \
           util/platformSpecific.py

TRANSLATIONS += resources/trufont_de.ts
