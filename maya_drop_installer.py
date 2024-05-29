import os
from pathlib import Path
import sys
import importlib

stop = False
try:
    import pymel.core as pc
except ImportError:
    from subprocess import check_call
    mayapy = Path(sys.executable).parent / "mayapy"
    result = check_call([str(mayapy), "-m", "pip", "install", "pymel==1.4"], shell=True) #, '"pymel==1.4"'])
    print(result)
    import pymel.core as pc
    


MAYA_APP_DIR = os.environ["MAYA_APP_DIR"]
MAYA_VERSION = pc.versions.shortName()
USER_SCRIPT_DIR = Path(MAYA_APP_DIR) / MAYA_VERSION / "scripts"
CAPITO_PATH = Path(__file__).parent
CAPITO_SETTINGS_DIR = "capito_settings"
SETUP_KEY = "CG_SCRIPTS_PATH"

sys.path.append(str(CAPITO_PATH))
maya_gui = importlib.import_module("capito.maya.ui.maya_gui")

msg_q = []


def sanity_checks():
    if not USER_SCRIPT_DIR.exists():
        return False
    msg_q.append(("info.png", f"User script dir: {USER_SCRIPT_DIR}"))
    return True

def create_settings_dir():
    if (USER_SCRIPT_DIR / CAPITO_SETTINGS_DIR).exists():
        msg_q.append(("info.png", f"Directory '{CAPITO_SETTINGS_DIR}' already exists in {USER_SCRIPT_DIR}."))
        return
    (USER_SCRIPT_DIR / CAPITO_SETTINGS_DIR).mkdir()
    msg_q.append(("confirm.png", f"Directory '{CAPITO_SETTINGS_DIR}' created in {USER_SCRIPT_DIR}"))

def create_userSetup():
    file_content = [
        "import sys",
        "import importlib",
        "import pymel.core as pc",
        f"sys.path.append(r'{str(CAPITO_PATH)}')",
        'importlib.import_module("capito.maya.setup")'
    ]
    user_setup = USER_SCRIPT_DIR / "userSetup.py"

    action = "Created"
    if user_setup.exists():
        result = pc.confirmDialog(
            title='Warning', message='userSetup.py already exists.\nReplace?',
            button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No'
        )
        if result == "No":
            msg_q.append(("error.png", "Copying of userSetup.py aborted by user."))
            msg_q.append(("info.png", "  -> Recommendation: Rename current userSetup.py, install again, compare and merge files."))
            return
        action = "Replaced"
    with open(user_setup, "w+") as cf:
        cf.write("\n".join(file_content))
    msg_q.append(("confirm.png", f"{action} userSetup.py in user script dir."))


def import_setup():
    importlib.import_module("capito.maya.setup")


def show_results():
    ratios = (30, 200)
    padding = 3
    with pc.window(title="Capito Installation Summary") as win:
        with pc.formLayout(numberOfDivisions=100) as fl:
            with pc.columnLayout(adj=True, bgc=[0, 0, 0]) as log_area:
                for msg in msg_q:
                    with pc.rowLayout(nc=2, cw=ratios):
                        pc.image(i=msg[0])
                        pc.text(label=msg[1])
            with pc.columnLayout(adj=True) as text_area:
                pc.text(
                    wordWrap=True, align="left",
                    label="""If there are no red messages you can try to run cg3 without restart.
To see if installation really worked properly a Maya restart is recommended.
If there are red messages follow the recommendations or contact admin."""
                )
            with pc.horizontalLayout() as button_area:
                pc.button(label="Exit Maya",
                            c=pc.Callback(pc.mel.eval, "quit"))
                close_button = pc.button(label="Try without Restart", c=import_setup)

    fl.attachForm(log_area, "top", padding)
    fl.attachForm(log_area, "left", padding)
    fl.attachForm(log_area, "right", padding)

    fl.attachForm(text_area, "left", 2 * padding)
    fl.attachForm(text_area, "right", 2 * padding)

    fl.attachForm(button_area, "bottom", padding)
    fl.attachForm(button_area, "left", padding)
    fl.attachForm(button_area, "right", padding)

    fl.attachControl(text_area, "bottom", padding, button_area)
    fl.attachControl(log_area, "bottom", padding, text_area)

    close_button.setCommand(pc.Callback(win.delete))
    
    win.show()
    win.setWidthHeight((600,200))
    maya_gui.center_window(win)


def onMayaDroppedPythonFile(*args, **kwargs):
    global msg_q
    msg_q = []
    if sanity_checks():
        create_settings_dir()
        create_userSetup()
        show_results()
    else:
        pc.confirmDialog(
            title='Installation Aborted', button=['OK'],
            message=f'Users "maya/scripts" directory doesn\'t exist.\nExpected at "{USER_SCRIPT_DIR}"'
        )
