"""UI for managing Asset Provider usage."""
import json
import os
from pathlib import Path

import capito.core.event as capito_event
from capito.conf.config import CONFIG
from capito.core.asset.providers import PROVIDERS
from capito.core.ui.decorators import bind_to_host
from PySide2 import QtCore  # pylint:disable=wrong-import-order
from PySide2.QtGui import QColor, QFont, QIcon, Qt  # pylint:disable=wrong-import-order
from PySide2.QtWidgets import (  # pylint:disable=wrong-import-order
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class GoogleDetailsWidget(QWidget):
    """Widget only visible when Google Sheets Provider is selected."""

    def __init__(self):
        super().__init__()

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        vbox.addWidget(QLabel("Google API Key JSON:"))

        api_key_hbox = QHBoxLayout()
        api_key_hbox.setContentsMargins(0, 0, 0, 0)
        self.api_key_lineedit = QLineEdit()
        self.api_key_lineedit.setText(CONFIG.GOOGLE_API_KEY_JSON)
        icon = self.style().standardIcon(QStyle.SP_DialogOpenButton)
        api_key_select_button = QPushButton("")
        api_key_select_button.setIcon(icon)
        api_key_select_button.setIconSize(QtCore.QSize(10, 10))
        api_key_select_button.setMaximumHeight(22)
        api_key_select_button.setMaximumWidth(22)
        api_key_select_button.clicked.connect(self._set_file)
        api_key_hbox.addWidget(self.api_key_lineedit)
        api_key_hbox.addWidget(api_key_select_button)

        vbox.addLayout(api_key_hbox)

        vbox.addWidget(QLabel("Google Sheet Name:"))
        self.sheet_name_lineedit = QLineEdit()
        self.sheet_name_lineedit.setText(CONFIG.GOOGLE_SHEETS_NAME)
        vbox.addWidget(self.sheet_name_lineedit)

        self.setLayout(vbox)

    def _set_file(self):
        key_file = QFileDialog.getOpenFileName(
            self,
            "Select API Key",
            str(Path(CONFIG.CAPITO_PROJECT_DIR) / "prefs"),
            "JSON file (*.json)",
        )
        self.api_key_lineedit.setText(key_file[0])

    @property
    def json_file(self):
        """Get the json key file."""
        return self.api_key_lineedit.text()

    @property
    def sheet_name(self):
        """Get the sheet name."""
        return self.sheet_name_lineedit.text()


@bind_to_host
class SetAssetProviderUI(QMainWindow):
    """The Capito Asset Provider Setup Window."""

    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asset Info Provider")
        self.choice = CONFIG.ASSET_PROVIDER_TYPE

        vbox = QVBoxLayout()

        vbox.addWidget(QLabel("Information base for your assets:"))

        self.provider_combobox = QComboBox()
        for provider_name in PROVIDERS:
            self.provider_combobox.addItem(provider_name)

        vbox.addWidget(self.provider_combobox)
        self.google_details_widget = GoogleDetailsWidget()
        vbox.addWidget(self.google_details_widget)
        vbox.addStretch()

        btnhbox = QHBoxLayout()
        btnhbox.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setMinimumWidth(100)
        ok_btn.clicked.connect(self._set_asset_provider)
        btnhbox.addWidget(ok_btn)

        vbox.addLayout(btnhbox)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

        self.provider_combobox.currentTextChanged.connect(self._selection_changed)
        self.provider_combobox.setCurrentText(CONFIG.ASSET_PROVIDER_TYPE)
        self._selection_changed(CONFIG.ASSET_PROVIDER_TYPE)

    def _selection_changed(self, choice: str):
        """When user changes combobox"""
        if choice == "Google Sheets Based":
            self.google_details_widget.show()
        else:
            self.google_details_widget.hide()

    def _set_asset_provider(self):
        """Write choice to CONFIG. Replace current Asset Provider in CONFIG."""
        if self._is_plausible():
            CONFIG.set(
                "capito_project",
                "ASSET_PROVIDER_TYPE",
                self.provider_combobox.currentText(),
            )
            CONFIG.set(
                "capito_project",
                "GOOGLE_API_KEY_JSON",
                self.google_details_widget.json_file,
            )
            CONFIG.set(
                "capito_project",
                "GOOGLE_SHEETS_NAME",
                self.google_details_widget.sheet_name,
            )
            CONFIG.save("capito_project")
            capito_event.post("asset_provider_changed")
            self.close()
            return

    def _is_plausible(self):
        provider = self.provider_combobox.currentText()
        if provider == "Google Sheets Based":
            json_file = self.google_details_widget.json_file
            sheet_name = self.google_details_widget.sheet_name
            if not json_file:
                self._message("Please supply a Google API Key JSON File.")
                return False
            if not Path(json_file).exists():
                self._message("Google API Key JSON File does not exist.")
                return False
            try:
                json.loads(Path(json_file).read_text(encoding="utf-8"))
            except PermissionError:
                self._message("Key JSON File not readable (Permissions).")
                return False
            except json.decoder.JSONDecodeError:
                self._message("Key JSON file is not a valid JSON.")
                return False
            if not sheet_name:
                self._message("Please specify the Sheet Name.")
                return False
            # TODO: Connection test (?)
        return True

    def _message(
        self,
        info: str,
        title="Error",
        message="Configuration Error",
        details: str = None,
    ):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setInformativeText(info)
        msg.setWindowTitle(title)
        if details:
            msg.setDetailedText(details)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
