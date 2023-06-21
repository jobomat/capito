from functools import partial

from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QHLine
from capito.haleres.ca_bridge import CABridge

from functools import cached_property


class AlignmentDelegate(QStyledItemDelegate):
    @cached_property
    def alignment(self):
        return dict()

    def set_column_alignment(self, column, alignment):
        self.alignment[column] = alignment

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        alignment = self.alignment.get(index.column(), None)
        if alignment is not None:
            option.displayAlignment = alignment


class FolderListWidget(QTreeWidget):
    folderDoubleClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpandsOnDoubleClick(False)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.setHeaderLabels(['Name', 'Size'])
        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        delegate = AlignmentDelegate(self)
        self.setItemDelegate(delegate)
        delegate.set_column_alignment(1, Qt.AlignRight)

    def addFolderItem(self, name):
        folder_item = QTreeWidgetItem(self)
        folder_item.setText(0, name)
        folder_item.setData(0, Qt.UserRole, "folder")
        icon = self.style().standardIcon(QStyle.SP_DirIcon)
        folder_item.setIcon(0, icon)

    def addFileItem(self, name, filesize):
        file_item = QTreeWidgetItem(self)
        file_item.setText(0, name)
        file_item.setText(1, filesize)
        font = file_item.font(1)
        font.setFamily("Courier")
        file_item.setFont(1, font)
        file_item.setData(0, Qt.UserRole, "file")
        icon = self.style().standardIcon(QStyle.SP_FileIcon)
        file_item.setIcon(0, icon)

    def mouseDoubleClickEvent(self, event):
        nameindex, sizeindex = self.selectedIndexes()
        itemdata = nameindex.model().itemData(nameindex)
        name = itemdata[0]
        typ = itemdata[256]
        if typ == "folder":
            self.folderDoubleClicked.emit(name)
        else:
            super().mouseDoubleClickEvent(event)

    def get_selected_items(self):
        selected_items = []
        for item in self.selectedItems():
            typ = item.data(0, Qt.UserRole)
            value = item.text(0)
            selected_items.append(f"{value}{'' if typ == 'file' else '/'}")
        return selected_items

class ShareButtonsWidget(QWidget):
    shareClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        hbox = QHBoxLayout()
        hbox.setMargin(0)

        for i in [1, 2, 3]:
            share = f"cg{i}"
            btn = QPushButton(share)
            btn.setMinimumWidth(80)
            btn.clicked.connect(partial(self.share_clicked_event, share))
            hbox.addWidget(btn)
        hbox.addStretch()

        self.setLayout(hbox)

    def share_clicked_event(self, share):
        self.shareClicked.emit(share)


class ActionButtonsWidget(QWidget):
    downloadClicked = Signal()
    deleteClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        hbox = QHBoxLayout()
        hbox.setMargin(0)

        hbox.addStretch()

        icon = self.style().standardIcon(QStyle.SP_ToolBarVerticalExtensionButton)
        download_btn = QPushButton(icon, "Download")
        download_btn.clicked.connect(partial(self.downloadClicked.emit))
        download_btn.setMinimumWidth(80)
        hbox.addWidget(download_btn)

        icon = self.style().standardIcon(QStyle.SP_DialogDiscardButton)
        delete_btn = QPushButton(icon, "Delete")
        delete_btn.clicked.connect(partial(self.deleteClicked.emit))
        delete_btn.setMinimumWidth(80)
        hbox.addWidget(delete_btn)

        self.setLayout(hbox)


class LocationWidget(QWidget):
    oneUpClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        hbox = QHBoxLayout()
        hbox.setMargin(0)

        icon = self.style().standardIcon(QStyle.SP_TitleBarShadeButton)
        up_btn = QPushButton(icon, "")
        hbox.addWidget(up_btn)
        up_btn.clicked.connect(partial(self.oneUpClicked.emit))

        self.current_folder_label = QLabel()
        hbox.addWidget(self.current_folder_label)

        hbox.addStretch()
        self.setLayout(hbox)


@bind_to_host
class HLRSBrowser(QMainWindow):
    def __init__(self, host: str=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HLRS Browser")
        self.setMinimumSize(400, 640)
        
        self.ca_bridge = CABridge()
        self.current_folder = ""

        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.list_widget = FolderListWidget(self)
        self.share_buttons_widget = ShareButtonsWidget(self)
        self.action_buttons_widget = ActionButtonsWidget(self)
        self.location_widget = LocationWidget(self)
        self.status_bar = QStatusBar()

    def _connect_widgets(self):
        self.list_widget.folderDoubleClicked.connect(self.on_folder_double_clicked)
        self.share_buttons_widget.shareClicked.connect(self.on_share_clicked)
        self.location_widget.oneUpClicked.connect(self.on_one_up_clicked)
        self.action_buttons_widget.downloadClicked.connect(self.on_download_clicked)

    def _create_layout(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.share_buttons_widget)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.action_buttons_widget)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.location_widget)
        vbox.addWidget(self.list_widget, stretch=1)
        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)
        self.setStatusBar(self.status_bar)

    def list_folder(self, folder:str=None):
        if folder:
            self.current_folder = f"{self.current_folder}/{folder}"
        else:
            self.current_folder = "/".join(self.current_folder.split("/")[:-1])
        self.status_bar.showMessage("Retrieving Folder List...")
        QApplication.processEvents()
        folder_content = self.ca_bridge.folder_listing(self.current_folder)
        self.list_widget.clear()
        for folder in folder_content["folders"]:
            self.list_widget.addFolderItem(folder)
        for file in folder_content["files"]:
            self.list_widget.addFileItem(file[0], file[1])
        self.status_bar.showMessage(f'{len(folder_content["folders"])} Folders, {len(folder_content["files"])} Files')

        self.location_widget.current_folder_label.setText(self.current_folder)

    def on_folder_double_clicked(self, folder_name):
        self.list_folder(folder_name)

    def on_share_clicked(self, share):
        self.current_folder = ""
        self.list_folder(share)
    
    def on_one_up_clicked(self):
        self.list_folder()

    def on_download_clicked(self):
        to_download = [f"{self.current_folder}/{f}" for f in self.list_widget.get_selected_items()]
        self.ca_bridge.rsync(to_download)


def main():
    HLRSBrowser()


if __name__ == "__main__":
    main()