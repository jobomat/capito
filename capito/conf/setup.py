from pathlib import Path
import os

from capito.core.ui.decorators import bind_to_host
from capito.core.file.utils import copytree
from capito.core.file.utils import sanitize_name
from capito.core.env import set_os_env_var
from capito.conf.config import CONFIG

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
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


def get_user_conf(username):
    """Get the json configurtion file of the currently active Capito User."""
    user_conf = Path(os.environ.get("CAPITO_PROJECT_DIR")) / "users" / username / "user_conf.json"
    if user_conf.exists():
        return user_conf


def get_project_conf():
    """Get the json configurtion file of the currently set Capito-Project."""
    project_conf = Path(os.environ.get("CAPITO_PROJECT_DIR")) / "capito_conf.json"
    if project_conf.exists():
        return project_conf


def get_user_names():
    """Returns a list of usernames of the current project.
    A username will only be included if a valid user_conf.json was found."""
    user_dir = Path(os.environ.get("CAPITO_PROJECT_DIR")) / "users"
    user_names = []
    for folder in user_dir.iterdir():
        if not folder.is_dir():
            continue
        user_conf = get_user_conf(folder.name)
        if not user_conf:
            continue
        user_names.append(folder.name)
    return user_names


@bind_to_host
class SetUserUI(QMainWindow):
    """The Capito User Setup Window."""

    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Capito User")
        self.choice = "existing"
        
        vbox = QVBoxLayout()

        vbox.addWidget(QLabel("Specify a Capito User:"))
        hbox = QHBoxLayout()
        existing_radiobtn = QRadioButton("Choose existing User")
        existing_radiobtn.setChecked(True)
        existing_radiobtn.toggled.connect(lambda:self.radio_checked("existing"))
        hbox.addWidget(existing_radiobtn)
        new_radiobtn = QRadioButton("Create New User")
        new_radiobtn.toggled.connect(lambda:self.radio_checked("new"))
        hbox.addWidget(new_radiobtn)
        vbox.addLayout(hbox)

        self.user_combobox = QComboBox()
        for user_name in get_user_names():
            self.user_combobox.addItem(user_name)

        vbox.addWidget(self.user_combobox)

        self.user_creation_lineedit = QLineEdit()
        suggestion = sanitize_name(QtCore.QDir().home().dirName())
        self.user_creation_lineedit.setText(suggestion)
        self.user_creation_lineedit.setPlaceholderText("Enter shortest possible name")
        self.user_creation_lineedit.hide()
        vbox.addWidget(self.user_creation_lineedit)

        vbox.addStretch()

        btnhbox = QHBoxLayout()
        btnhbox.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setMinimumWidth(100)
        ok_btn.clicked.connect(self.set_or_create_user)
        btnhbox.addWidget(ok_btn)
        vbox.addLayout(btnhbox)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def radio_checked(self, choice:str):
        self.choice = choice
        if choice == "new":
            self.user_combobox.hide()
            self.user_creation_lineedit.show()
        else:
            self.user_creation_lineedit.hide()
            self.user_combobox.show()

    def set_or_create_user(self):
        """Create: Create user dir + user_conf.json
        Create and Set: Set the CAPITO_USERNAME env var to the current user."""
        if self.choice == "new":
            username = sanitize_name(self.user_creation_lineedit.text())
            template = Path(os.environ.get("CAPITO_BASE_DIR")) / "resources" / "templates" / "user_dir"
            dst = Path(os.environ.get("CAPITO_PROJECT_DIR")) / "users" / username
            copytree(template, dst)
        else:
            username = self.user_combobox.currentText()

        set_os_env_var("CAPITO_USERNAME", username)
        CONFIG.load(get_user_conf(os.environ.get("CAPITO_USERNAME")), "capito_user")
        self.close()


def set_capito_project(path: Path):
    """Sets a capito project given the top folder of the project.
    The given path must be a valid capito project!
    This function will NOT CHECK if the given path is a valid caption project!
    """
    set_os_env_var("CAPITO_PROJECT_DIR", str(path))
    project_conf = get_project_conf()
    
    if project_conf:
        CONFIG.reset()
        CONFIG.load(project_conf, "capito_project")
    
        if os.environ.get("CAPITO_USERNAME"):
            user_conf = get_user_conf(os.environ.get("CAPITO_USERNAME"))
            if user_conf:
                CONFIG.load(user_conf, "capito_user")
            else:
                # username env var exists, but user is not user in this project.
                SetUserUI() 
        else:
            # username env var does not yet exist.
            SetUserUI() 
    else:
        # No config file found (should be impossible... only if race condition occured.)
        print("Project conf not found.")


def create_capito_project(path: Path, name:str, template:Path=None):
    """Create a capito project folder named 'name' in 'path'.
    Use the template project structure 'template'."""
    template = template or Path(os.environ.get("CAPITO_BASE_DIR")) / "resources" / "templates" / "capito_project"
    dst = path / name
    copytree(template, dst)
    set_capito_project(dst)
    

@bind_to_host
class SetupUI(QMainWindow):
    """The Capito mini starter window."""

    def __init__(self, host: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Capito Setup")
        
        vbox = QVBoxLayout()

        vbox.addWidget(QLabel("No Capito Project set."), stretch=1)

        existing_btn = QPushButton("Set an existing Project...")
        existing_btn.clicked.connect(self.set_existing)
        new_btn = QPushButton("Create a new Project...")
        new_btn.clicked.connect(self.create_new)

        vbox.addWidget(existing_btn)
        vbox.addWidget(new_btn)
        
        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def set_existing(self):
        result = QFileDialog.getExistingDirectory(
            self, "Choose Project Folder",
            QtCore.QDir().home().path(),
            QFileDialog.Option.ShowDirsOnly
        )
        if result:
            project_conf = Path(result) / "capito_conf.json"
            if not project_conf:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("This seems to be no valid Capito Project.")
                msg.setWindowTitle("Oops")
                msg.setDetailedText(f"The folder {result} contains no valid 'capito_conf.json' file.")
                msg.setStandardButtons(QMessageBox.Ok)
                return
            set_capito_project(Path(result))
            self.close()

    def create_new(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select folder where project folder will be created",
            QtCore.QDir().home().path(),
            QFileDialog.Option.ShowDirsOnly
        )
        listed_name = sanitize_name(f"{QtCore.QDir().home().dirName()}s_project")
        while True:
            name, ok = QInputDialog().getText(
                self, "Set project name",
                "Project name:", QLineEdit.Normal,
                listed_name
            )
            if not ok:
                break
            name = sanitize_name(name)
            listed_name = name
            full_path = Path(path) / name
            if full_path.exists():
                qm = QMessageBox()
                ret = qm.question(self,'Oops', f"A folder named {name} already exists.\nPlease choose another name.", qm.Ok)
                continue
            else:
                break

        if path and ok and name:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setText("The project will be created here:")
            msg.setInformativeText(f"{path}/{name}")
            msg.setWindowTitle("Create Capito Project")
            msg.setDetailedText(f"A folder called {name} will be created in {path}.\n\nThis folder will contain further dirs and files.\n\nAdditionally a user environment variable called 'CAPITO_PROJECT_DIR' will be created.\n\nThis variable will point to the created directory.")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            # msg.buttonClicked.connect(self.create)

            confirm = msg.exec_()
        
            if confirm == 1024:
                create_capito_project(Path(path), name)
                self.close()
