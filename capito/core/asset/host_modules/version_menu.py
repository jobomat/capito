"""Module for importing host specific Modules and creating QWidgets"""
import importlib

from PySide2.QtWidgets import QWidget


def version_menu_factory(parent):
    try:
        mod = importlib.import_module(
            f"capito.core.asset.host_modules.{parent.parent.host}_version_menu"
        )
        return mod.MayaVersionMenu(parent)
    except ImportError as error:
        print(error)
        widget = QWidget()
        widget.hide()
        return widget
