"""Module for importing host specific Modules and creating QWidgets"""
import importlib

from PySide2.QtWidgets import QWidget

def reveal_button_factory(parent_widget):
    try:
        mod = importlib.import_module(
            f"capito.core.asset.host_modules.{parent_widget.parent_widget.host}_reveal_button"
        )
        return mod.RevealButton(parent_widget)
    except ImportError as error:
        print(error)
        widget = QWidget()
        widget.hide()
        return widget
