"""Module for importing host specific Modules and creating QWidgets"""
import importlib

from PySide2.QtWidgets import QWidget

def reveal_button_factory(parent_widget):
    try:
        host = parent_widget.parent_widget.host
        mod = importlib.import_module(
            f"capito.core.asset.host_modules.{host}.{host}_reveal_button"
        )
        return mod.RevealButton(parent_widget)
    except ImportError as error:
        print(error)
        widget = QWidget()
        widget.hide()
        return widget


def detail_actions_widget_factory(parent_widget):
    try:
        host = parent_widget.parent_widget.host
        mod = importlib.import_module(
            f"capito.core.asset.host_modules.{host}.{host}_detail_actions_widget"
        )
        return mod.DetailActionsWidget(parent_widget)
    except ImportError as error:
        print(error)
        widget = QWidget()
        widget.hide()
        return widget