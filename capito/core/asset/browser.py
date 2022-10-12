"""The ui for Asset Browsing"""
from capito.conf.setup import SetupUI, SetUserUI
from capito.core.asset.browse_widgets import BrowseWidget
from capito.core.asset.input_widgets import InputWidget
from capito.core.asset.publish_widgets import PublishWidget
from capito.core.pipe.ui import PipeManager
from capito.core.ui.decorators import bind_to_host
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QFont, QIcon, Qt  # pylint:disable=wrong-import-order
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QAction,
    QMainWindow,
    QMenu,
    QMenuBar,
    QTabWidget,
)


@bind_to_host
class AssetBrowser(QMainWindow):
    """The main Capito window."""

    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.host = host

        self.setMinimumSize(1024, 768)
        self.setWindowTitle("Capito")

        self._create_actions()
        self._connect_actions()
        self._create_menu_bar()
        self._create_ui()

    def _create_ui(self):
        """Tie everything together"""
        self.tab_widget = QTabWidget(self)

        tab_index_1 = self.tab_widget.addTab(BrowseWidget(self.host), "Browse")
        self.tab_widget.setTabIcon(tab_index_1, QIcon("icons:asset_circle.svg"))
        self.tab_widget.setIconSize(QtCore.QSize(28, 28))

        if self.host != "system":
            tab_index_2 = self.tab_widget.addTab(InputWidget(self.host), "Input")
            self.tab_widget.setTabIcon(tab_index_2, QIcon("icons:in.svg"))
            self.tab_widget.setIconSize(QtCore.QSize(28, 28))

            tab_index_3 = self.tab_widget.addTab(PublishWidget(self.host), "Publish")
            self.tab_widget.setTabIcon(tab_index_3, QIcon("icons:out.svg"))
            self.tab_widget.setIconSize(QtCore.QSize(28, 28))

        self.setCentralWidget(self.tab_widget)

    def _create_menu_bar(self):
        """Add menu items here."""
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        project_menu = QMenu("&Project", self)
        menu_bar.addMenu(project_menu)
        project_menu.addAction(self.set_create_action)
        project_menu.addAction(self.change_user_action)

        tool_menu = QMenu("&Tools", self)
        menu_bar.addMenu(tool_menu)
        tool_menu.addAction(self.open_pipe_action)

    def _create_actions(self):
        """Add actions for menus (and other controls) here."""
        self.set_create_action = QAction("&Set / Create Project...", self)
        self.change_user_action = QAction("&Change User...", self)
        self.open_pipe_action = QAction("&Pipe Editor...", self)

    def _connect_actions(self):
        """Connect actions to the function/class calls."""
        self.set_create_action.triggered.connect(SetupUI)
        self.change_user_action.triggered.connect(SetUserUI)
        self.open_pipe_action.triggered.connect(PipeManager)
