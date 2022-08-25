from PySide2 import QtCore, QtWidgets
from capito.core.ui import constants
from capito.core.helpers import detect_host


def bind_to_host(ui_class):
    def wrapper(*args, **kwargs):
        host = detect_host()
        if host == "maya":
            import maya.app.general.mayaMixin as maya_mixin
            import maya.OpenMayaUI as omui
            import shiboken2

            main_window_ptr = omui.MQtUtil.mainWindow()
            maya_win = shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

            class M(maya_mixin.MayaQWidgetDockableMixin, ui_class):
                def __init__(self):
                    super().__init__(*args, **kwargs, parent=maya_win, host=host)

            ui = M()
            ui.show(dockable=True)

        if host == "nuke":
            from PySide2 import QtWidgets
            nuke_win = QtWidgets.QApplication.instance().activeWindow()
            class N(ui_class):
                def __init__(self):
                    super().__init__(*args, **kwargs, parent=nuke_win, host=host)

            ui = N()
            ui.show()

        if host == "substance_painter":
            import substance_painter
            substance_win = substance_painter.ui.get_main_window()
            class S(ui_class):
                def __init__(self):
                    super().__init__(*args, **kwargs, parent=substance_win, host=host)

            ui = S()
            ui.show()
        
        if host == "substance_designer":
            import sd
            app = sd.getContext().getSDApplication()
            ui_mngr = app.getQtForPythonUIMgr()
            substance_win = ui_mngr.getMainWindow()
            class S(ui_class):
                def __init__(self):
                    super().__init__(*args, **kwargs, parent=substance_win, host=host)

            ui = S()
            ui.show()
            
        elif host == "system":
            app = QtWidgets.QApplication([])
            app.setStyle("Fusion")
            app.setPalette(constants.dark_palette)
            ui = ui_class(host=host)
            ui.show()
            app.exec_()

    return wrapper