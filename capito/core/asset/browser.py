"""The ui for Asset Browsing"""
from capito.core.pipe.ui import PipeManager
from capito.conf.setup import SetupUI, SetUserUI
from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QHLine, QSplitWidget

from capito.core.asset.browse_widgets import BrowseWidget
from capito.core.asset.input_widgets import InputWidget
from capito.core.asset.publish_widgets import PublishWidget

from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QFont, QIcon, Qt  # pylint:disable=wrong-import-order
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QAbstractItemView,
    QAction,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabBar,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


@bind_to_host
class AssetBrowser(QMainWindow):
    """The main Capito window."""

    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.host = host

        self.setMinimumSize(1024, 768)

        self._createActions()
        self._connectActions()
        self._createMenuBar()
        self._createUI()
        
    def _createUI(self):
        self.tab_widget = QTabWidget(self)

        tab_index_1 = self.tab_widget.addTab(BrowseWidget(), "Browse")
        self.tab_widget.setTabIcon(tab_index_1, QIcon("icons:asset_circle.svg"))
        self.tab_widget.setIconSize(QtCore.QSize(28, 28))

        if self.host != "system":
            tab_index_2 = self.tab_widget.addTab(InputWidget(), "Input")
            self.tab_widget.setTabIcon(tab_index_2, QIcon("icons:in.svg"))
            self.tab_widget.setIconSize(QtCore.QSize(28, 28))

            tab_index_3 = self.tab_widget.addTab(PublishWidget(), "Publish")
            self.tab_widget.setTabIcon(tab_index_3, QIcon("icons:out.svg"))
            self.tab_widget.setIconSize(QtCore.QSize(28, 28))

        self.setCentralWidget(self.tab_widget)

    def _createMenuBar(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        project_menu = QMenu("&Project", self)
        menu_bar.addMenu(project_menu)
        project_menu.addAction(self.set_create_action)
        project_menu.addAction(self.change_user_action)

        tool_menu = QMenu("&Tools", self)
        menu_bar.addMenu(tool_menu)
        tool_menu.addAction(self.open_pipe_action)

    def _createActions(self):
        self.set_create_action = QAction("&Set / Create Project...", self)
        self.change_user_action = QAction("&Change User...", self)
        self.open_pipe_action = QAction("&Pipe Editor...", self)

    def _connectActions(self):
        self.set_create_action.triggered.connect(SetupUI)
        self.change_user_action.triggered.connect(SetUserUI)
        self.open_pipe_action.triggered.connect(PipeManager)
