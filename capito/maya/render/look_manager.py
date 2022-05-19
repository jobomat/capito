"""Provide GUIs for managing Looks."""
# import os

# import PySide2.QtCore as QtCore
# import PySide2.QtGui as QtGui
# import PySide2.QtWidgets as QtWidgets
# from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

# ICON_DIR = "C:/Users/jobo/Documents/GoogleDrive/coding/python/cg3/maya/icons/cmt"
# _LOOKMANAGER_WIN = None


# class LookManagerUI(MayaQWidgetBaseMixin, QtWidgets.QMainWindow):
#     """GUI for managing looks in Maya"""

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.setAttribute(QtGui.Qt.WA_DeleteOnClose)
#         toolbar = self.addToolBar("Tools")
#         action = toolbar.addAction("Run All Tests")
#         action.setIcon(
#             QtGui.QIcon(QtGui.QPixmap(os.path.join(ICON_DIR, "cmt_run_all_tests.png"))))
#         # action.triggered.connect(self.run_all_tests)
#         action.setToolTip("Run all tests.")

#         action = toolbar.addAction("Run Selected Tests")
#         action.setIcon(
#             QtGui.QIcon(QtGui.QPixmap(os.path.join(
#                 ICON_DIR, "cmt_run_selected_tests.png")))
#         )
#         action.setToolTip("Run all selected tests.")
#         # action.triggered.connect(self.run_selected_tests)

#         action = toolbar.addAction("Run Failed Tests")
#         action.setIcon(
#             QtGui.QIcon(QtGui.QPixmap(os.path.join(
#                 ICON_DIR, "cmt_run_failed_tests.png")))
#         )
#         action.setToolTip("Run all failed tests.")
#         # action.triggered.connect(self.run_failed_tests)

#         action = toolbar.addAction("Refresh Tests")
#         action.setIcon(QtGui.QIcon(QtGui.QPixmap(":/refresh.png")))
#         action.setToolTip("Refresh the test list all failed tests.")
#         # action.triggered.connect(self.refresh_tests)

#         widget = QtWidgets.QWidget()
#         self.setCentralWidget(widget)
#         vbox = QtWidgets.QVBoxLayout(widget)

#         splitter = QtWidgets.QSplitter(orientation=QtGui.Qt.Horizontal)
#         self.test_view = QtWidgets.QTreeView()
#         self.test_view.setSelectionMode(
#             QtWidgets.QAbstractItemView.ExtendedSelection)
#         splitter.addWidget(self.test_view)
#         splitter.addWidget(QtWidgets.QTreeView())
#         vbox.addWidget(splitter)
#         splitter.setStretchFactor(1, 4)

#     def closeEvent(self, event):  # pylint: disable=fixme, invalid-name
#         """Close event to clean up everything."""
#         global _LOOKMANAGER_WIN  # pylint: disable=fixme, global-statement
#         _LOOKMANAGER_WIN = None


# def show():
#     """Shows the manager window."""
#     global _LOOKMANAGER_WIN  # pylint: disable=fixme, global-statement
#     if _LOOKMANAGER_WIN:
#         _LOOKMANAGER_WIN.close()
#     _LOOKMANAGER_WIN = LookManagerUI()
#     _LOOKMANAGER_WIN.show()
from functools import partial

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
    QInputDialog,
    QTextEdit,
    QScrollArea,
    QSpacerItem,
    QSizePolicy
)

import pymel.core as pc

from capito.core.ui.decorators import bind_to_host
from capito.core.ui.widgets import QSplitWidget, QHLine
from capito.maya.render.looks import list_look_nodes, Look


@bind_to_host
class LookManager(QMainWindow):
    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)

        self.setMinimumSize(400, 400)

        vbox = QVBoxLayout()

        toolbox = QHBoxLayout()
        import_btn = QPushButton("Import Look")
        import_btn.clicked.connect(self.import_look)
        toolbox.addWidget(import_btn)
        create_btn = QPushButton("Create Look for Selection")
        create_btn.clicked.connect(self.create_look)
        toolbox.addWidget(create_btn)
        refresh_btn = QPushButton("Refresh Look List")
        refresh_btn.clicked.connect(self.refresh_look_list)
        toolbox.addWidget(refresh_btn)
        vbox.addLayout(toolbox)

        self.look_list = QListWidget()
        vbox.addWidget(self.look_list)
        
        button_box = QHBoxLayout()
        select_btn = QPushButton("Select Objects")
        select_btn.clicked.connect(self.select_objects)
        button_box.addWidget(select_btn)
        assign_btn = QPushButton("Assign to Selection")
        assign_btn.clicked.connect(self.assign)
        button_box.addWidget(assign_btn)
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export)
        button_box.addWidget(export_btn)
        delete_btn = QPushButton("Del")
        delete_btn.clicked.connect(self.delete)
        button_box.addWidget(delete_btn)
        vbox.addLayout(button_box)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)
        
        self.refresh_look_list()

    def refresh_look_list(self):
        self.look_list.clear()
        for look_node in list_look_nodes():
            item = QListWidgetItem(f"{look_node.lookName.get()} ({look_node.name()})")
            item.setData(Qt.UserRole, Look(look_node))
            self.look_list.addItem(item)



    def import_look(self):
        filename = QFileDialog.getOpenFileName(
            self, "Import Look", f"{str(pc.workspace.path)}", filter="Maya ASCII (*.ma)"
        )
        if not filename[0]:
            return

        pc.system.importFile(filename[0])
        self.refresh_look_list()

    def create_look(self):
        name, ok = QInputDialog.getText(self, 'Create Look', 'Enter Look Name:')
        if ok:
            sel = pc.selected()
            l = Look(name)
            l.read(sel)
            self.refresh_look_list()

    def select_objects(self):
        items = self.look_list.selectedItems()
        for item in items:
            look = item.data(Qt.UserRole)
            look.select_objects()
    
    def assign(self):
        items = self.look_list.selectedItems()
        for item in items:
            look = item.data(Qt.UserRole)
            look.assign(pc.selected())

    def export(self):
        items = self.look_list.selectedItems()
        for item in items:
            look:Look = item.data(Qt.UserRole)
            filename = QFileDialog.getSaveFileName(
                self, "Export Look", f"{str(pc.workspace.path)}/{look.name}.ma", filter="Maya ASCII (*.ma)"
            )
            if not filename[0]:
                return
            look.select_shading_groups()
            pc.system.exportSelected(filename[0], type="mayaAscii")

    def delete(self):
        items = self.look_list.selectedItems()
        for item in items:
            look = item.data(Qt.UserRole)
            look.select_objects()
            pc.mel.eval("sets -e -forceElement initialShadingGroup;")
            
            to_delete = []
            shading_groups = look.shadingGroups
            for sg in shading_groups:
                for attr in ("aiSurfaceShader", "aiVolumeShader", "surfaceShader", "displacementShader", "volumeShader"):
                    to_delete.extend(sg.attr(attr).listHistory())
            to_delete.append(look.look_node)

            pc.delete(set(to_delete))
        self.refresh_look_list()

            