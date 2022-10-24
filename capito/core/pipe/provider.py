"""Module providing the core publishing class."""
import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from capito.conf.config import CONFIG

from .models import Pipeable, PipeableCategory


def get_pipeable_project_modules():
    """Get pipeable_module folders for each host
    CAPITO_PROJECT_DIR/code/pipeable_modules/HOST
    CAPITO_PROJECT_DIR/users/CAPITO_USERNAME/code/pipeable_modules/HOST
    """
    folders = []
    project_dir = CONFIG.CAPITO_PROJECT_DIR

    if project_dir:
        project_path = Path(project_dir)
        if project_path.exists():
            project_modules = project_path / "flows" / "pipeable_modules"
            folders.append(str(project_modules))
            user_modules = (
                project_path / "users" / CONFIG.CAPITO_USERNAME / "pipeable_modules"
            )
            if user_modules.exists():
                folders.append(str(user_modules))
    return folders


class PipeProvider:
    """PipeProvider loads and provides pipeable modules."""

    def __init__(self, hosts: List = None, module_folders: List[str] = None):
        self.hosts = ["system"]
        self.module_folders = []

        self.modules: Dict[str, Tuple[Any, Pipeable]] = {}

        if hosts is not None:
            self.hosts.extend(hosts)

        # add std modules
        self.add_module_folder(Path(__file__).parent / "pipeable_modules")
        # add project and user modules:
        for folder in get_pipeable_project_modules():
            self.add_module_folder(folder)
        # add any additional provided modules:
        if module_folders:
            for mf in module_folders:
                self.add_module_folder(mf)

        self.load_modules()

    def add_module_folder(self, module_folder: str):
        """Add additional module folders."""
        path = Path(module_folder)
        for host in [h for h in self.hosts if h is not None]:
            module_folder = path / host
            if module_folder.exists():
                self.module_folders.append(str(module_folder))

    def load_modules(self):
        """initiate module loading in given folders and host subfolders."""
        for folder in self.module_folders:
            if folder not in sys.path:
                sys.path.append(folder)
            self.load_modules_in_folder(folder)

    def load_modules_in_folder(self, folder):
        """load all detected modules in folder"""
        path = Path(folder)
        for pyfile in path.glob("*.py"):
            modname = pyfile.name[:-3]
            try:
                pipe_module = importlib.import_module(f"{modname}")
                class_instance = getattr(pipe_module, modname)()
                class_instance.set_default_parameters()
                self.modules[modname] = (pipe_module, class_instance)
            except AttributeError as error:
                print(f"Module '{modname}' could not be loaded: AttributeError")
                print(error.__traceback__)
            except:
                print(f"An error occured while loading module '{modname}'.")

    def get_instance(self, module_name: str):
        """Given a pipeable module name the function returns an instance of the pipeable."""
        class_instance = getattr(self.modules[module_name][0], module_name)()
        class_instance.set_default_parameters()
        return class_instance

    def list_categories(self):
        """Return a list of all categories that are currently in provider list"""
        return list(set([mod[1].category for mod in self.modules.values()]))

    def list_filtered_modules(
        self, categories: List[PipeableCategory] = None, hosts: list = None
    ):
        """Retrun a filtered list by category and host."""
        return [
            mod
            for mod in self.modules.values()
            if mod[1].host in hosts and mod[1].category in categories
        ]
