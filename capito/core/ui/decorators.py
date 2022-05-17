from PySide2 import QtCore, QtWidgets
from capito.core.ui import constants


def bind_to_host(ui_class):
    def wrapper(*args, **kwargs):
        try:
            import maya.app.general.mayaMixin as maya_mixin
            import maya.OpenMayaUI as omui
            import shiboken2

            main_window_ptr = omui.MQtUtil.mainWindow()
            maya_win = shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

            class M(maya_mixin.MayaQWidgetDockableMixin, ui_class):
                def __init__(self):
                    super().__init__(*args, **kwargs, parent=maya_win, host="maya")

            ui = M()
            ui.show(dockable=True)

        except ImportError:
            app = QtWidgets.QApplication([])
            app.setStyle("Fusion")
            app.setPalette(constants.dark_palette)
            ui = ui_class(host="system")
            ui.show()
            app.exec_()

    return wrapper