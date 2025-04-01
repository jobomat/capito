from collections import defaultdict

from PySide6 import QtCore, QtWidgets, QtGui
from shiboken6 import wrapInstance
import maya.OpenMayaUI as omui

import pymel.core as pc


# window_map is a collection of maya window-names / ids 
window_map = {
    'About Arnold Window': 'AboutArnold',
    'Arnold Render View': 'ArnoldRenderView',
    'Arnold Licence Window': 'ArnoldLicense',
    'Blind Data Editor': 'blindDataEditor1Window',
    'Boss Editor': 'BossEditorMainWindow',
    'Channel Control': 'LockingKeyable',
    'Clip Editor': 'clipEditorPanel1Window',
    'Color Prefs': 'colorPreferenceWindow',
    'Component Editor': 'componentEditorPanel1Window',
    'Connection Editor': 'connectWindow',
    'Content Browser': 'contentBrowserPanel1Window',
    'Create Render Node': 'createRenderNodeWindow',
    'Dope Sheet': 'dopeSheetPanel1Window',
    'Expression Editor': 'expressionEditorWin',
    'Graph Editor': 'graphEditor1Window',
    'Hypergraph': 'hyperGraphPanel1Window',
    'Hypershade': 'hyperShadePanel1Window',
    'Hotkey Editor': 'HotkeyEditor',
    'Light Editor': 'MayaLightEditorWindowWorkspaceControl',
    'Namespace Editor': 'namespaceEditor',
    'Node Editor': 'nodeEditorPanel1Window',
    'Option Box Window': 'OptionBoxWindow',
    'Outliner': 'outlinerPanel1Window',
    'Plugin Manager': 'pluginManagerWindow',
    'Pose Editor': 'posePanel1Window',
    'Preferences': 'PreferencesWindow',
    'Project Window': 'projectWindow',
    'Quick Rig Window': 'quickRigWindowId',
    'Relationship Editor': 'relationshipPanel1Window',
    'Render Settings': 'unifiedRenderGlobalsWindow',
    'Render Setup': 'MayaRenderSetupWindowWorkspaceControl',
    'Script Editor': 'scriptEditorPanel1Window',
    'Set Driven Key Editor': 'setDrivenWnd',
    'Shape Editor': 'shapePanel1Window',
    'Shelf Editor': 'shelfEditor',
    'Show Inputs Window': 'showHistoryWindow',
    'Time Editor': 'timeEditorPanel1Window',
    'TX Manager': 'txman_winWorkspaceControl',
    'Tool Settings': 'ToolSettings',
    'UV ToolKit': 'UVToolkitDockControl',
    'UV View': 'polyTexturePlacementPanel1Window',
    'Module Manager': 'module_manager_win'
}

# # Search for window names:    
# mmw = maya_main_window()

# search_string = "MayaLightEditorWindow"
# for child in mmw.findChildren(QtWidgets.QWidget):
#     widget_string = str(child)
#     if search_string in widget_string:
#         print(str(child))
#         print(child.parent().parent())

# # check if it was a hit
# import pymel.core as pc

# name = "MayaLightEditorWindow"
# print(pc.workspaceControl(name, q=True, exists=True))
# print(pc.window(name, q=True, exists=True))


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


def get_mouse_position():
    cursor_pos = QtGui.QCursor.pos()
    return cursor_pos.x(), cursor_pos.y() 
    # Convert the mouse position to screen coordinates
    # screen_pos = maya_main_window().mapFromGlobal(cursor_pos)
    # Retrieve the pixel coordinates
    # return screen_pos.x(), screen_pos.y()


def reposition(win_id, position=[0, 0]):
    global window_map
    try:
        pc.window(window_map[win_id], edit=True, iconify=False)
        pc.window(window_map[win_id], edit=True, topLeftCorner=position)
        return True
    except RuntimeError:
        return False


def gather(position=[0, 0], *args):
    global window_map
    repositioned = []
    skipped = []
    for nice_name, ui_name in window_map.items():
        if reposition(ui_name, position):
            repositioned.append(nice_name)
        else:
            skipped.append(nice_name)
    return reposition, skipped


def collect_info(*args):
    global window_map
    infos = defaultdict(dict)
    attributes = ['leftEdge', 'topEdge', 'width', 'height', 'iconify']
    for nice_name, ui_name in window_map.items():
        found = False
        try:
            if pc.window(ui_name, q=True, exists=True):
                found = True
                if (pc.workspaceControl(ui_name, q=True, exists=True) and not pc.workspaceControl(ui_name, q=True, vis=True)):
                    found = False
            if not found:
                continue
            for attr in attributes:
                arg = {attr: True}
                infos[nice_name][attr] = pc.window(ui_name, q=True, **arg)
        except RuntimeError:
           pass
    return infos


class WindowManager:
    def __init__(self):
        self.window_name = "window_manager"
        self.btn_color = [
            (0.857,0.539,0.256), (0.657,0.857,0.256),
            (.5,.5,.5),(0.207,0.559,0.740), (0.740,0.332,0.202)
        ]

        self.gui()
    
    def gui(self):
        if pc.window(self.window_name, q=True, exists=True):
            pc.deleteUI(self.window_name)

        with pc.window(self.window_name, title="Maya Window Manager") as win:
            with pc.columnLayout(adj=True):
                pc.button(label="Search / Refresh Open Windows...", c=self.build_win_list)
                with pc.columnLayout(adj=True) as self.win_list:
                    pass    
            self.build_win_list()

        win.setWidth(350)
        x, y = get_mouse_position()
        win.setTopLeftCorner((y, x))

    def build_win_list(self, *args):
        for child in self.win_list.getChildren():
            pc.deleteUI(child)
        for win_name, attrs in collect_info().items():
            with pc.rowLayout(nc=5, adj=1, cal=(1, "left"), parent=self.win_list) as row:
                pc.text(
                    label=win_name, font="boldLabelFont",
                    annotation=f"UI name: {window_map[win_name]}"
                )
                iconify_btn = pc.button(
                    label="Maximize" if attrs['iconify'] else "Minimize",
                    w=60, bgc=self.btn_color[attrs['iconify']],
                )
                to_front_btn = pc.button(
                    label="To Front",
                    w=60, bgc=self.btn_color[2]
                )
                pc.button(
                    label="To (0,0)", w=46, bgc=self.btn_color[3],
                    annotation=f"Current (left | top): {attrs['leftEdge']} | {attrs['topEdge']}",
                    c=pc.Callback(reposition, win_name)
                )
                close_btn = pc.button(
                    label="Close", w=46, bgc=self.btn_color[4])
            to_front_btn.setCommand(
                pc.Callback(self.to_front, win_name, iconify_btn)
            )
            iconify_btn.setCommand(
                pc.Callback(self.toggle_iconify, win_name, iconify_btn)
            )
            close_btn.setCommand(pc.Callback(
                self.close_win, win_name, row))

    def to_front(self, win_name, iconify_btn):
        global window_map
        pc.window(window_map[win_name], e=True, iconify=True)
        pc.window(window_map[win_name], e=True, iconify=False)
        iconify_btn.setBackgroundColor(self.btn_color[0])

    def toggle_iconify(self, win_name, btn):
        global window_map
        iconify = pc.window(window_map[win_name], q=True, iconify=True)
        pc.window(window_map[win_name], e=True, iconify=not iconify)
        btn.setBackgroundColor(self.btn_color[not iconify])
        btn.setLabel("Maximize" if not iconify else "Minimize")

    def close_win(self, win_name, row):
        global window_map
        if pc.workspaceControl(window_map[win_name], q=True, exists=True):
            pc.workspaceControl(window_map[win_name], e=True, vis=0)
        elif pc.window(window_map[win_name], q=True, exists=True):
            pc.deleteUI(window_map[win_name])
        pc.deleteUI(row)
                #pc.button(label="Gather at [0,0]", c=pc.Callback(gather))


class WinWrapper:
    def __init__(self, window_name, window_title, padding=5, verticalScrollBarAlwaysVisible=True):
        self.window_name = window_name
        self.window_title = window_title
        self.padding = padding
        self.vsb = verticalScrollBarAlwaysVisible

        self.main_fl = None
        self.top_container = None
        self.mid_container = None
        self.bottom_container = None

        self.build()

    def build(self):
        if pc.window(self.window_name, q=True, exists=True):
            pc.deleteUI(self.window_name)

        with pc.window(self.window_name, title=self.window_title) as self.win:
            with pc.formLayout(numberOfDivisions=100) as self.main_fl:
                with pc.columnLayout(adj=True) as self.top_container:
                    pass
                with pc.scrollLayout(childResizable=True, vsb=self.vsb) as self.mid_container:
                    pass
                with pc.columnLayout(adj=True) as self.bottom_container:
                    pass

        self.main_fl.attachForm(self.top_container, "top", self.padding)
        self.main_fl.attachForm(str(self.top_container), "left", self.padding)
        self.main_fl.attachForm(str(self.top_container), "right", self.padding)

        self.main_fl.attachForm(str(self.mid_container), "left", self.padding)
        self.main_fl.attachForm(str(self.mid_container), "right", self.padding)

        self.main_fl.attachForm(
            str(self.bottom_container), "left", self.padding)
        self.main_fl.attachForm(
            str(self.bottom_container), "right", self.padding)
        self.main_fl.attachForm(
            str(self.bottom_container), "bottom", self.padding)

        self.main_fl.attachControl(
            self.mid_container, "top", self.padding, self.top_container
        )
        self.main_fl.attachControl(
            self.mid_container, "bottom", self.padding, self.bottom_container
        )
        self.main_fl.attachNone(self.top_container, "bottom")
        self.main_fl.attachNone(self.bottom_container, "top")

    def add_top_layout(self, layout, **kwargs):
        pc.setParent(self.top_container)
        return layout(**kwargs)

    def add_mid_layout(self, layout, **kwargs):
        pc.setParent(self.mid_container)
        return layout(**kwargs)

    def add_bottom_layout(self, layout, **kwargs):
        pc.setParent(self.bottom_container)
        return layout(**kwargs)

    def close(self, *args):
        print(f"CLOSING {self.window_name}")
        pc.deleteUI(self.window_name)
"""
import cg3.ui.windows as win

print(win.collect_info())
win.reposition("Graph Editor")
"""
