import pymel.core as pc

from capito.maya.ui import maya_gui
from capito.conf.config import CONFIG
from capito.core.asset.browser import AssetBrowser


def win_manager_factory():
    from capito.maya.ui import windows

    windows.WindowManager()


def module_manager_factory():
    from capito.maya.util.devtools import ModuleManager

    ModuleManager()


def attribute_finder_factory():
    from capito.maya.util.pminspect import AttributeFinder

    AttributeFinder()


def test_runner_factory():
    import capito.maya.test.mayaunittestui as mayatestui

    mayatestui.show()


def toolbox_button_pressed():
    if CONFIG.CAPITO_PROJECT:
        AssetBrowser()
        return
    print("Call set or create Capito project.")

# btn=maya_gui.add_toolbox_button(
#     style="iconOnly",
#     i="dev.png",
#     annotation="cg3 Development Helpers"
# )

btn = maya_gui.add_toolbox_button(
    command=pc.Callback(toolbox_button_pressed),
    style="iconOnly",
    i="hdm.png",
)

dev_menu_items = {
    "Window Manager": win_manager_factory,
    "Module Manager": module_manager_factory,
    "Node Inspector": attribute_finder_factory,
    "Test Runner": test_runner_factory,
}
with pc.popupMenu(parent=btn, button=3):
    for menu, cmd in dev_menu_items.items():
        pc.menuItem(menu, c=pc.Callback(cmd))
