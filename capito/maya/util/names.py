import pymel.core as pc
from os.path import split
import re

save_char_map = {
    'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
    ' ': '_', '.': '_', ',': '_', ':': '_'
}


def get_legal_character(char, allow=""):
    if re.match(f"[a-zA-Z_0-9{allow}]", char):
        return char
    else:
        return save_char_map.get(char, "_")


def legalize_text(text, allow=""):
    return "".join([get_legal_character(c, allow) for c in text])


def name_with_numbered_postfix(name: str, postfix: str, zerofill: int = 2) -> str:
    """"
    Adds the specified postfix to 'name'.
    If 'name' already ends with a number, the number will be incremented.
    The number will be filled with leading zeros to the length of zerofill.
    If no leading zeros should be applied set zerofill to a falsy value.
    """
    pattern = f".*{postfix}(?P<num>\d*)$"
    match = re.match(pattern, name)
    if match:
        name = name[:-(len(postfix))]
        if match.groupdict()["num"]:
            num = str(int(match.groupdict()["num"]) + 1)
            num_len = len(match.groupdict()["num"])
            name = name[:-num_len]
            zerofill = zerofill or num_len
            postfix = f"{postfix}{num.zfill(num_len)}"
        else:
            postfix = f"{postfix}{'2'.zfill(zerofill)}"
    return f"{name}{postfix}"


def hash_iterator(name_pattern, start=1, step=1, hashlen=3):
    parts = re.split("#+", name_pattern)
    if len(parts) > 1:
        hashlen = len(re.search("#+", name_pattern).group())
    else:
        parts.append("")
    while True:
        yield "".join(
            [parts[0], str(start).zfill(hashlen)] + parts[1:]
        )
        start += step


def get_namespace(filepath, namespace_map={}):
    filename = split(filepath)[-1].split(".")[0]
    return namespace_map.get(filename, None) or filename


class HashRenamer():
    def __init__(self):
        self.name_history = []

        self.template = pc.uiTemplate('HashRenamerTemplate', force=True)
        self.template.define(
            pc.window, widthHeight=[300, 24], toolbox=True,
            title="Hash Renamer", resizeToFitChildren=True
        )

        self.ui()

    def ui(self):
        win_name = "hash_renamer_win"
        if pc.window(win_name, exists=True):
            pc.deleteUI(win_name)

        with self.template:
            with pc.window():
                with pc.columnLayout(adjustableColumn=True):
                    self.name_textFieldGrp = pc.textField(
                        textChangedCommand=self.check_text_field_input,
                        enterCommand=self.hash_rename_sel,
                        alwaysInvokeEnterCommandOnReturn=True,
                        annotation="'spine_##_jnt' will be renamed to\n'spine_01_jnt', 'spine_02_jnt'...",
                        placeholderText="Type and press Enter to rename."
                    )
                    self.name_history_menu = pc.popupMenu()
                    for name in self.name_history:
                        pc.menuItem(label=name, c=pc.Callback(
                            self.name_textFieldGrp.setText, name))

    def check_text_field_input(self, *args):
        if not len(args[0]):
            return ""
        self.name_textFieldGrp.setText(
            "{}{}".format(
                args[0][:-1],
                get_legal_character(args[0][-1], allow="#")
            )
        )

    def hash_rename_sel(self, *args):
        sel = pc.selected()
        if not sel:
            pc.warning("Please select some objects to rename.")
            return

        name = hash_iterator(args[0])
        for obj in sel:
            obj.rename(next(name))

        self.name_textFieldGrp.setText("")

        self.name_history.append(args[0])
        pc.menuItem(
            label=args[0], parent=self.name_history_menu,
            c=pc.Callback(self.name_textFieldGrp.setText, args[0])
        )
