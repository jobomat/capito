from functools import partial
import json
from pathlib import Path

from PySide2 import QtCore
from PySide2.QtGui import QColor, QFont, QIcon, Qt
from PySide2.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
    QToolButton,
    QLineEdit,
    QCheckBox,
    QFileDialog,
    QTextEdit
)

from capito.core.pipe import Pipeable, PipePlayer, PipeProvider
from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QSplitWidget, QHLine
from capito.core.ui.syntax import PythonHighlighter


PipeColors = {
    "maya": QColor(30, 30, 30),
    "system": QColor(30, 30, 30),
    "Check": QColor(40, 60, 40),
    "Export": QColor(0, 83, 79),
    "Collect": QColor(20, 40, 60),
    "default": QColor(45, 45, 45),
}


class ItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.decorationPosition = QStyleOptionViewItem.Right
        super().paint(painter, option, index)


class IterableListWidget(QListWidget):
    def __init__(self):
        super().__init__()

    def iterAllItems(self) -> QListWidgetItem:
        for i in range(self.count()):
            yield self.item(i)

    def getIndex(self, wanted_item: QListWidgetItem) -> int:
        for i, item in enumerate(self.iterAllItems()):
            if wanted_item == item:
                return i


class ListItemWithButton(QWidget):
    def __init__(self, item: QListWidgetItem, parent=None):
        super().__init__(parent)
        self.item = item
        module = self.item.data(Qt.UserRole)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QLabel(f" {module.category}: {module.label}"))
        row.addStretch(1)
        self.setStyleSheet("QToolButton::hover {background-color : #cc0000;}")
        btn = QToolButton()
        btn.setIcon(QIcon('icons:trash.svg'))
        row.addWidget(btn)
        self.setLayout(row)

        btn.clicked.connect(self.delete)

    def delete(self):
        i = self.item.listWidget().getIndex(self.item)
        self.item.listWidget().takeItem(i)


class AddModuleWindow(QWidget):
    def __init__(self, parent=None, callback=None, provider: PipeProvider = None):
        super().__init__(parent)
        self.setWindowTitle("Add Modules")
        self.setFixedSize(300, 600)
        preferred_order = ["Collect", "Check", "Export"]
        mod_categories = []
        availible_categories = provider.list_categories()
        for mod_type in preferred_order:
            if mod_type in availible_categories:
                mod_categories.append(mod_type)

        self.callback = callback

        self.widget_layout = QVBoxLayout()
        self.list_widget = CategorizedModulesListWidget(provider=provider)

        self.widget_layout.addWidget(self.list_widget)

        btn = QPushButton("Add")
        btn.clicked.connect(self.add)
        self.widget_layout.addWidget(btn)

        self.setLayout(self.widget_layout)

    def add(self):
        self.callback(self.list_widget.selectedItems())
        self.close()


class CategorizedModulesListWidget(QListWidget):
    def __init__(self, provider: PipeProvider = None, preferred_order = ["Collect", "Check", "Export"]):
        super().__init__()    
        mod_categories = []
        availible_categories = provider.list_categories()
        for mod_type in preferred_order:
            if mod_type in availible_categories:
                mod_categories.append(mod_type)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSpacing(1)

        type_font = QFont()
        type_font.setPointSize(10)
        type_font.setBold(True)
        host_font = QFont()
        host_font.setPointSize(11)
        host_font.setBold(True)
        for host in provider.hosts:
            host_item = QListWidgetItem()
            host_item.setText(f"{host.capitalize()}")
            host_item.setFont(host_font)
            host_item.setBackgroundColor(PipeColors.get(host, PipeColors["default"]))
            host_item.setFlags(host_item.flags() ^ QtCore.Qt.ItemIsSelectable)
            host_item.setTextAlignment(QtCore.Qt.AlignHCenter)
            self.addItem(host_item)
            for mod_category in mod_categories:
                type_item = QListWidgetItem()
                type_item.setText(f" {mod_category}")
                type_item.setFlags(type_item.flags() ^ QtCore.Qt.ItemIsSelectable)
                type_item.setFont(type_font)
                type_item.setBackgroundColor(
                    PipeColors.get(mod_category, PipeColors["default"])
                )
                type_item.setIcon(QIcon(f"icons:{mod_category.lower()}.svg"))
                self.addItem(type_item)
                for mod in provider.list_filtered_modules(
                    categories=[mod_category], hosts=[host]
                ):
                    class_instance = mod[1]
                    item = QListWidgetItem()
                    item.setText(f"        {class_instance.label}")
                    item.setBackgroundColor(QColor(40, 40, 40))
                    # item.setBackgroundColor(PipeColors.get(mod_type, PipeColors["default"]))
                    item.setData(Qt.UserRole, class_instance)
                    self.addItem(item)
    
    def mousePressEvent(self, event):
        """Clear selection when empty area is clicked."""
        item = self.indexAt(event.pos())
        if not item.isValid():
            self.clearSelection()  
        QListWidget.mousePressEvent(self, event)
                    

class EditableModulesListWidget(IterableListWidget):
    def __init__(self):
        super().__init__()
        #self.setItemDelegate(ItemDelegate())

        # Enable drag & drop ordering of items.
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def add_modules(self, selected_items):
        for selected_item in selected_items:
            item = QListWidgetItem()
            pipeable_instance = selected_item.data(Qt.UserRole).get_instance()
            print(pipeable_instance.category.capitalize())
            item.setData(Qt.UserRole, pipeable_instance)
            item.setBackground(PipeColors[pipeable_instance.category.capitalize()])
            row = ListItemWithButton(item=item)
            item.setSizeHint(row.minimumSizeHint())
            self.addItem(item)
            self.setItemWidget(item, row)

    def update_playlist_status(self, current_item: Pipeable):
        for item in self.iterAllItems():
            if item.data(Qt.UserRole) is current_item:
                if current_item.failed:
                    item.setIcon(QIcon("icons:failed.svg"))
                else:
                    item.setIcon(QIcon("icons:passed.svg"))
    
    def mousePressEvent(self, event):
        """Clear selection when empty area is clicked."""
        item = self.indexAt(event.pos())
        if not item.isValid():
            self.clearSelection()  
        QListWidget.mousePressEvent(self, event)
        self.currentRowChanged

@bind_to_host
class PipeManager(QMainWindow):
    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        hosts = []
        if host != "system":
            hosts.append(host)
        self.provider = PipeProvider(hosts=hosts)
        self.player = PipePlayer(self.provider, [self.update_playlist_status])

        self.add_window = AddModuleWindow(
            callback=self.add_modules, provider=self.provider, parent=parent
        )

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        load_playlist_button = QPushButton("Load Playlist")
        load_playlist_button.clicked.connect(self.load_playlist)
        load_playlist_button.setIcon(QIcon("icons:open.svg"))
        hbox.addWidget(load_playlist_button)
        add_modules_button = QPushButton("Add Modules")
        add_modules_button.setIcon(QIcon("icons:add.svg"))
        add_modules_button.clicked.connect(self.open_add_window)
        hbox.addWidget(add_modules_button)
        export_playlist_button = QPushButton("Save Playlist")
        export_playlist_button.setIcon(QIcon("icons:save.svg"))
        export_playlist_button.clicked.connect(self.save_playlist)
        hbox.addWidget(export_playlist_button)
        play_button = QPushButton("Play")
        play_button.setIcon(QIcon("icons:play.svg"))
        play_button.clicked.connect(self.play)
        hbox.addWidget(play_button)

        self.edit_layout_container = QVBoxLayout()
        self.edit_layout = QVBoxLayout()
        self.edit_layout_container.addLayout(self.edit_layout)
        self.edit_layout_container.addStretch()

        module_list_vbox = QVBoxLayout()
        self.module_list_widget = EditableModulesListWidget()
        self.module_list_widget.itemSelectionChanged.connect(self.load_edit_layout)
        module_list_vbox.addWidget(self.module_list_widget)

        split_widget = QSplitWidget(module_list_vbox, self.edit_layout_container, ratio=(1, 2))
        #split_layout = QVBoxLayout()
        #split_layout.addWidget(split_widget)
        
        vbox.addLayout(hbox)
        vbox.addWidget(QHLine())
        vbox.addWidget(split_widget, 1)

        central_widget = QWidget()
        central_widget.setLayout(vbox)

        self.setCentralWidget(central_widget)

        self.load_edit_layout()

    def open_add_window(self):
        self.add_window.show()

    def load_playlist(self):
        filename = QFileDialog.getOpenFileName(
            self, "Playlist Filename", filter="JSON (*.json)"
        )
        if not filename[0]:
            return
        playlist_file = Path(filename[0])
        with playlist_file.open("r") as json_file:
            loaded_list = json.load(json_file)
        self.player.reset()
        self.player.append_from_list(loaded_list["playlist"])
        self.player.title = playlist_file.stem
        self.player.description = loaded_list["description"]
        for module in self.player.playlist:
            item = QListWidgetItem()
            item.setData(Qt.UserRole,module)
            item.setBackground(PipeColors[module.category.capitalize()])
            row = ListItemWithButton(item=item)
            item.setSizeHint(row.minimumSizeHint())
            self.module_list_widget.addItem(item)
            self.module_list_widget.setItemWidget(item, row)
        self.load_edit_layout()
        self.reset_playlist_status()

    def save_playlist(self):
        filename = QFileDialog.getSaveFileName(
            self, "Save Playlist as", filter="JSON (*.json)"
        )
        if not filename[0]:
            return
        self.create_playlist()
        with open(filename[0], "w") as json_file:
            to_save = {
                "description": self.player.description,
                "playlist": self.player.as_list()
            }
            json.dump(to_save, json_file, indent=4)

    def load_edit_layout(self):
        self.clear_edit_layout()
        selected_items = self.module_list_widget.selectedItems()
        if not selected_items:
            self.load_playlist_info()
            return

        class_instance = selected_items[0].data(Qt.UserRole)
        headline_font = QFont()
        headline_font.setPointSize(10)
        headline_font.setBold(True)
        label = QLabel(f"{class_instance.category}: {class_instance.label}")
        label.setFont(headline_font)
        self.edit_layout.addWidget(label)
        self.edit_layout.addWidget(QLabel(str(class_instance.__doc__)))
        self.edit_layout.addWidget(QHLine())

        param_group_box = QGroupBox("Parameters")
        param_group_box.setStyleSheet("QGroupBox {font-weight: bold;fontsize: 14px;}")
        param_form_layout = QFormLayout()
        
        stop_on_failed_checkbox = QCheckBox()
        stop_on_failed_checkbox.setChecked(class_instance.stop_on_failed)
        stop_on_failed_checkbox.stateChanged.connect(
            partial(self.change_stop_on_failed, class_instance)
        )
        param_form_layout.addRow(QLabel("Stop on Fail"), stop_on_failed_checkbox)

        for parameter, value in class_instance.get_parameters().items():
            change_function = partial(self.change_parameter, class_instance, parameter)
            if isinstance(value, bool):
                value_edit = QCheckBox()
                value_edit.setChecked(value)
                value_edit.stateChanged.connect(change_function)
            else:
                value_edit = QLineEdit()
                value_edit.setText(value)
                value_edit.textChanged.connect(change_function)
            value_edit.setToolTip(class_instance.get_parameter_help(parameter))
            param_form_layout.addRow(QLabel(parameter), value_edit)
        
        param_group_box.setLayout(param_form_layout)
        self.edit_layout.addWidget(param_group_box)

    def change_parameter(self, class_instance, parameter, *args):
        setattr(class_instance, parameter, args[0])
        self.reset_playlist_status()

    def change_stop_on_failed(self, class_instance, *args):
        class_instance.stop_on_failed = args[0]

    def clear_edit_layout(self):
        index = self.edit_layout.count()
        while(index > 0):
            index -= 1
            child = self.edit_layout.itemAt(index).widget()
            child.setParent(None)

    def load_playlist_info(self):
        headline_font = QFont()
        headline_font.setPointSize(10)
        headline_font.setBold(True)

        label = QLabel(self.player.title)
        label.setFont(headline_font)
        self.edit_layout.addWidget(label)

        self.edit_layout.addWidget(QLabel("Description:"))

        description = QTextEdit()
        description.setText(self.player.description)
        description.textChanged.connect(partial(self.description_changed, description))
        self.edit_layout.addWidget(description)

        self.edit_layout.addWidget(QLabel("Globals:"))

        global_textedit = QTextEdit()
        highlight = PythonHighlighter(global_textedit.document())
        self.edit_layout.addWidget(global_textedit)

    def description_changed(self, description_textfield:QTextEdit):
        self.player.description = description_textfield.toPlainText()


    def add_modules(self, selected_items):
        for selected_item in selected_items:
            item = QListWidgetItem()
            pipeable_instance = self.provider.get_instance(selected_item.data(Qt.UserRole).name)
            item.setData(Qt.UserRole,pipeable_instance)
            item.setBackground(PipeColors[pipeable_instance.category.capitalize()])
            row = ListItemWithButton(item=item)
            item.setSizeHint(row.minimumSizeHint())
            self.module_list_widget.addItem(item)
            self.module_list_widget.setItemWidget(item, row)
        self.load_edit_layout()
        self.reset_playlist_status()

    def play(self):
        self.create_playlist()
        self.player.play()

    def create_playlist(self):
        self.player.reset()
        for item in self.module_list_widget.iterAllItems():
            self.player.append_existing(item.data(Qt.UserRole))

    def update_playlist_status(self, current_item: Pipeable):
        for item in self.module_list_widget.iterAllItems():
            if item.data(Qt.UserRole) is current_item:
                if current_item.failed:
                    if current_item.stop_on_failed:
                        item.setIcon(QIcon("icons:failed.svg"))
                    else:
                        item.setIcon(QIcon("icons:warning.svg"))
                else:
                    item.setIcon(QIcon("icons:passed.svg"))

    def reset_playlist_status(self):
        for item in self.module_list_widget.iterAllItems():
            item.setIcon(QIcon("icons:pending.svg"))
        