"""Provide GUIs for managing Looks."""
import os

import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

ICON_DIR = "C:/Users/jobo/Documents/GoogleDrive/coding/python/cg3/maya/icons/cmt"
_LOOKMANAGER_WIN = None


class LookManagerUI(MayaQWidgetBaseMixin, QtWidgets.QMainWindow):
    """GUI for managing looks in Maya"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(QtGui.Qt.WA_DeleteOnClose)
        toolbar = self.addToolBar("Tools")
        action = toolbar.addAction("Run All Tests")
        action.setIcon(
            QtGui.QIcon(QtGui.QPixmap(os.path.join(ICON_DIR, "cmt_run_all_tests.png"))))
        # action.triggered.connect(self.run_all_tests)
        action.setToolTip("Run all tests.")

        action = toolbar.addAction("Run Selected Tests")
        action.setIcon(
            QtGui.QIcon(QtGui.QPixmap(os.path.join(
                ICON_DIR, "cmt_run_selected_tests.png")))
        )
        action.setToolTip("Run all selected tests.")
        # action.triggered.connect(self.run_selected_tests)

        action = toolbar.addAction("Run Failed Tests")
        action.setIcon(
            QtGui.QIcon(QtGui.QPixmap(os.path.join(
                ICON_DIR, "cmt_run_failed_tests.png")))
        )
        action.setToolTip("Run all failed tests.")
        # action.triggered.connect(self.run_failed_tests)

        action = toolbar.addAction("Refresh Tests")
        action.setIcon(QtGui.QIcon(QtGui.QPixmap(":/refresh.png")))
        action.setToolTip("Refresh the test list all failed tests.")
        # action.triggered.connect(self.refresh_tests)

        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)
        vbox = QtWidgets.QVBoxLayout(widget)

        splitter = QtWidgets.QSplitter(orientation=QtGui.Qt.Horizontal)
        self.test_view = QtWidgets.QTreeView()
        self.test_view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        splitter.addWidget(self.test_view)
        splitter.addWidget(QtWidgets.QTreeView())
        vbox.addWidget(splitter)
        splitter.setStretchFactor(1, 4)

    def closeEvent(self, event):  # pylint: disable=fixme, invalid-name
        """Close event to clean up everything."""
        global _LOOKMANAGER_WIN  # pylint: disable=fixme, global-statement
        _LOOKMANAGER_WIN = None


def show():
    """Shows the manager window."""
    global _LOOKMANAGER_WIN  # pylint: disable=fixme, global-statement
    if _LOOKMANAGER_WIN:
        _LOOKMANAGER_WIN.close()
    _LOOKMANAGER_WIN = LookManagerUI()
    _LOOKMANAGER_WIN.show()
