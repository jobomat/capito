import sys

import pymel.core as pc

from capito.maya.ui.windows import WindowManager, WinWrapper


class ModuleManager(WinWrapper):
    def __init__(self):
        super().__init__("module_manager_win", "Module Manager")
        self.filter = "capito."

        self.top = self.add_top_layout(pc.horizontalLayout)
        self.filter_textFieldGrp = pc.textFieldGrp(
            label="Filter Modules",
            text=self.filter,
            tcc=self.set_filter,
            parent=self.top,
            adj=2,
        )
        self.top.redistribute()
        self.mid = self.add_mid_layout(pc.columnLayout, adj=True)
        self.module_list_layout = pc.columnLayout(adj=True, parent=self.mid)

        self.bottom = self.add_bottom_layout(pc.horizontalLayout)
        pc.button(label="Toggle Selection", parent=self.bottom, c=self.toggle_selection)
        pc.button(label="Delete Selected", parent=self.bottom, c=self.delete_selected)
        pc.button(label="Refresh", parent=self.bottom, c=self.build_module_list_layout)
        self.bottom.redistribute()

        self.build_module_list_layout()

    def build_module_list_layout(self, *args):
        for child in self.module_list_layout.getChildren():
            pc.deleteUI(child)
        for mod in sys.modules.keys():
            if self.filter in mod:
                with pc.rowLayout(
                    parent=self.module_list_layout, nc=3, adj=2, cal=(2, "left")
                ) as row:
                    pc.checkBox(w=20)
                    pc.text(label=mod)
                    pc.button(
                        label="Delete", w=40, c=pc.Callback(self.del_module, mod, row)
                    )

    def set_filter(self, *args):
        if len(args[0]) < 3:
            return
        for child in self.module_list_layout.getChildren():
            pc.deleteUI(child)
        self.filter = args[0]
        self.build_module_list_layout()

    def del_module(self, module, row):
        if not module in sys.modules:
            return
        print(f"Reloading {module}")
        del sys.modules[module]
        pc.deleteUI(row)

    def toggle_selection(self, *args):
        for row in self.module_list_layout.getChildren():
            checkbox, text, btn = row.getChildren()
            checkbox.setValue(not checkbox.getValue())

    def delete_selected(self, *args):
        for row in self.module_list_layout.getChildren():
            checkbox, text, _ = row.getChildren()
            if checkbox.getValue():
                self.del_module(text.getLabel(), row)


class DevToolsWindow:
    def __init__(self):
        self.window_name = "devToolsWindow"
        self.gui()

    def gui(self):
        if pc.window(self.window_name, exists=True):
            pc.deleteUI(self.window_name)
        with pc.window(self.window_name, title="cg3 Dev Tools") as win:
            with pc.columnLayout(adj=True):
                pc.button(label="Window Manager", c=pc.Callback(WindowManager))
                pc.button(label="Module Manager", c=pc.Callback(ModuleManager))
