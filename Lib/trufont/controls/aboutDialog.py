import os
import platform
import subprocess

from PyQt5.Qt import PYQT_VERSION_STR, QT_VERSION_STR
from PyQt5.QtCore import QEvent, QSize, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from trufont import __file__ as modulePath
from trufont import __version__

try:
    PATH = os.path.abspath(os.path.join(modulePath, "../../.."))
    gitShortHash = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=PATH, stderr=subprocess.DEVNULL
    ).decode()
    gitShortLog = subprocess.check_output(
        ["git", "shortlog", "-sn"], cwd=PATH, stderr=subprocess.DEVNULL
    ).decode()
    with open(os.path.join(PATH, "COPYRIGHT"), encoding="utf-8") as fd:
        licenseText = fd.read()
    licenseText = "<p>{}</p>".format(
        licenseText.replace("\n\n", "</p><p>").replace("\n", " ")
    )
    with open(os.path.join(PATH, "THANKS"), encoding="utf-8") as fd:
        thanksText = fd.read()
    thanksText = "<p>{}</p>".format(
        thanksText.replace("\n\n", "</p><p>").replace("\n–", "<br>–").replace("\n", " ")
    )
except Exception:
    gitShortHash = gitShortLog = licenseText = thanksText = ""


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.MSWindowsFixedSizeDialogHint
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowCloseButtonHint,
        )
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(self.tr("About"))

        app = QApplication.instance()
        name = app.applicationName()
        domain = app.organizationDomain()

        iconLabel = QLabel(self)
        iconLabel.setAlignment(Qt.AlignCenter)
        iconLabel.setMaximumWidth(250)
        iconLabel.setMinimumSize(250, 210)
        icon = self.windowIcon()
        size = icon.actualSize(QSize(186, 186))
        iconLabel.setPixmap(icon.pixmap(size))
        titleLabel = QLabel(self)
        titleLabel.setText(
            self.tr(
                "<p style='color: #353535; font-size: 24pt; font-weight: 250'>"
                "TruFont Font Editor</p>"
                "<p style='font-size: 13pt; font-weight: 400'>{} Pristine Wax</p>"
            ).format(__version__)
        )
        textLabel = QLabel(self)
        text = self.tr(
            "<p>{n} is a free and open source font editor and scripting "
            "environment made by the developers of the {n} community.</p>"
            "<p>{n} is built upon the "
            "<a href='http://ts-defcon.readthedocs.org/en/ufo3/' "
            "style='color: #356FDE'>defcon</a> UFO library and exposes a "
            "<a href='http://robofab.com/' style='color: #356FDE'>robofab</a>"
            "-like API for scripting purposes.</p>"
            "<p>Running on Qt {} (PyQt {}).</p>"
            "<p>Version {} {} – Python {}."
        ).format(
            QT_VERSION_STR,
            PYQT_VERSION_STR,
            __version__,
            gitShortHash,
            platform.python_version(),
            n=name,
        )
        if domain:
            text += self.tr(
                "<br>See <a href='http://{d}' style='color: #356FDE'>{d}</a> "
                "for more information.</p>"
            ).format(d=domain)
        else:
            text += "</p>"
        textLabel.setText(text)
        textLabel.setOpenExternalLinks(True)
        textLabel.setWordWrap(True)

        authorsLabel = QTextBrowser(self)
        authorsLabel.setText("\n".join(self.authors()))

        licenseLabel = QTextBrowser(self)
        licenseLabel.setText(licenseText)

        thanksLabel = QTextBrowser(self)
        thanksLabel.setText(thanksText)

        self.stackWidget = QStackedWidget(self)
        self.stackWidget.addWidget(textLabel)
        self.stackWidget.addWidget(authorsLabel)
        self.stackWidget.addWidget(licenseLabel)
        self.stackWidget.addWidget(thanksLabel)

        textLayout = QVBoxLayout()
        textLayout.setContentsMargins(0, 14, 16, 16)
        textLayout.addWidget(titleLabel)
        textLayout.addWidget(self.stackWidget)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        textLayout.addWidget(spacer)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(iconLabel)
        mainLayout.addLayout(textLayout)

        frame = QFrame()
        frame.setMinimumHeight(54)
        frame.setMaximumHeight(54)
        frame.setStyleSheet("background: rgb(230, 230, 230)")

        buttonsLayout = QHBoxLayout(frame)
        for index, text in enumerate(("Authors", "License", "Credits")):
            label = QLabel(text, self)
            label.setAlignment(Qt.AlignCenter)
            label.setCursor(Qt.PointingHandCursor)
            label.setProperty("index", index + 1)
            label.setStyleSheet("color: #356FDE; text-decoration: underline")
            label.installEventFilter(self)
            buttonsLayout.addWidget(label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(mainLayout)
        layout.addWidget(frame)

    def authors(self):
        for line in gitShortLog.splitlines():
            elem = line.split("\t")[1]
            if not elem or elem.startswith("=?") or elem.endswith("bot"):
                continue
            yield elem

    # ----------
    # Qt methods
    # ----------

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            index = obj.property("index")
            if index is not None:
                if self.stackWidget.currentIndex() == index:
                    index = 0
                self.stackWidget.setCurrentIndex(index)
                return True
            return False
        return super().eventFilter(obj, event)

    def sizeHint(self):
        return QSize(600, 314)
