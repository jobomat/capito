"""Module for the asset browser qt signal."""

from capito.core.asset.models import Asset, Step, Version
from PySide2 import QtCore  # pylint:disable=wrong-import-order


class Signals(QtCore.QObject):
    """Special Signals for communicating between custom Widgets"""

    filter_changed = QtCore.Signal(str, bool)
    asset_selected = QtCore.Signal(Asset)
    step_selected = QtCore.Signal(Step)
    version_added = QtCore.Signal(Version)
    version_selected = QtCore.Signal(Version)
    version_changed = QtCore.Signal(Version)

    def __init__(self):
        super().__init__()
