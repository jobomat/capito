from pathlib import Path
from typing import Any, Dict, List

from capito.core.pipe import Pipeable, PipeableCategory
from PySide6.QtWidgets import QDialog  # pylint:disable=wrong-import-order
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class InputExampleDialog(QDialog):
    """A complicated version of QConfirmDialog."""

    def __init__(self, question, message_text, ok_btn_text, reject_btn_text):
        super().__init__()
        self.message_text = message_text
        self.setModal(True)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(question))
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        ok_btn = QPushButton(ok_btn_text)
        ok_btn.clicked.connect(self.return_values)
        hbox.addWidget(ok_btn)

        reject_btn = QPushButton(reject_btn_text)
        reject_btn.clicked.connect(self.reject)
        hbox.addWidget(reject_btn)

        self.setLayout(vbox)
        self.show()

    def return_values(self):
        self.message_text = self.message_text
        self.accept()


class InputExample(Pipeable):
    """Example for Pipe Blocking User Input."""

    label = "User Input Example"
    category = PipeableCategory.INPUT
    host = "system"

    def execute(self, items: List[Any], exports: List[str], user_input: Dict[str, Any]):
        modal = InputExampleDialog(
            self.question, self.message_text, self.ok_btn_text, self.reject_btn_text
        )
        if modal.exec_():
            self.messages.append(modal.message_text)
        else:
            self.failed = True
            self.messages.append(f"Aborted by user.")

    def set_parameters(
        self, question: str, message_text: str, ok_btn_text: str, reject_btn_text: str
    ):
        self.question = question
        self.message_text = message_text
        self.ok_btn_text = ok_btn_text
        self.reject_btn_text = reject_btn_text

    def get_default_parameters(self):
        """Default parameters."""
        return {
            "question": "Do you wish to continue?",
            "message_text": "The user agreed to continue.",
            "ok_btn_text": "Yes",
            "reject_btn_text": "No",
        }

    def get_parameter_help(self, parameter):
        help = {
            "question": "The question to show in the dialog.",
            "message_text": "The text handed to the registered reporters.",
            "ok_btn_text": "The text displayed on the OK button.",
            "reject_btn_text": "The text displayed on the REJECT button.",
        }

        return help.get(parameter, super().get_parameter_help(parameter))
