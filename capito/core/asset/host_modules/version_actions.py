"""Module for importing host specific Modules and creating QWidgets"""
import importlib

from PySide2.QtWidgets import QWidget


def version_menu_factory(parent_widget):
    try:
        host = parent_widget.parent_widget.host
        mod = importlib.import_module(
            f"capito.core.asset.host_modules.{host}.{host}_version_menu"
        )
        return mod.VersionMenu(parent_widget)
    except ImportError as error:
        print(error)
        widget = QWidget()
        widget.hide()
        return widget


def version_context_actions_factory(parent_widget):
    try:
        host = parent_widget.parent_widget.host
        mod = importlib.import_module(
            f"capito.core.asset.host_modules.{host}.{host}_version_context_actions"
        )
        return mod.version_context_actions(parent_widget)
    except ImportError as error:
        print(error)
        return []