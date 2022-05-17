import os
import ast
import json
from collections import defaultdict

import pymel.core as pc

from capito.core.file.utils import silent_remove, silent_rename


def all_the_same(items):
    return all(x == items[0] for x in items)


def keep_keys(dictionary, keep_list):
    return {k: v for k, v in dictionary.items() if k in keep_list}


# def ascii_encode_dict(data):
#     ascii_encode = lambda x: x.encode('ascii') if isinstance(x, unicode) else x 
#     return dict(map(ascii_encode, pair) for pair in data.items())


class TopLevelShelf():
    name = pc.language.getMelGlobal('string', 'gShelfTopLevel')
    shelf_dir = pc.mel.eval("internalVar -userShelfDir")

    def get_shelf_names(self):
        return pc.shelfTabLayout(self.name, q=True, childArray=True)

    def shelf_exists(self, shelf_name):
        return shelf_name in self.get_shelf_names()

    def delete_shelf(self, shelf_name):
        if self.shelf_exists(shelf_name):
            pc.deleteUI(pc.shelfLayout(shelf_name, q=True, fullPathName=True))
            deleted_shelf_name = os.path.join(
                self.shelf_dir, "shelf_{}.mel.deleted".format(shelf_name)
            )
            silent_remove(deleted_shelf_name)
            silent_rename(
                os.path.join(self.shelf_dir, "shelf_{}.mel".format(shelf_name)),
                deleted_shelf_name
            )

    def add_shelf(self, shelf_name, replace=False):
        exists = self.shelf_exists(shelf_name)
        if exists and not replace:
            pc.warning("Shelf '{}' already exists. Choose another name or set 'replace' to True.".format(shelf_name))
            return False
        else:
            if exists:
                self.delete_shelf(shelf_name)
            pc.shelfLayout(shelf_name, parent=self.name)
            return True
        
    def add_button(self, shelf_name, flags):
        if flags.get("type", "") == "separator":
            del(flags["type"])
            self.add_separator(shelf_name, **flags)
            return
        flags["image"] = flags.get("image", "commandButton.png")

        pc.shelfButton(
            parent="{}|{}".format(self.name, shelf_name),
            **flags
        )

    def delete_button(self, shelf_name, i):
        btns = self.get_button_names(shelf_name)
        if i < len(btns):
            pc.deleteUI(btns[i])

    def add_separator(self, shelf_name, flags=None):
        if not flags:
            flags = {"style": "shelf", "horizontal": False, "width": 5}
        pc.separator(
            parent="{}|{}".format(self.name, shelf_name),
            **flags
        )

    def get_button_names(self, shelf_name):
        return pc.shelfLayout(
            "{}|{}".format(self.name, shelf_name),
            q=True, childArray=True, fullPathName=True
        )

    def save(self):
        pc.mel.eval('saveAllShelves $gShelfTopLevel;')

    def move_tab(self, shelf_name, pos, relative=False):
        all_shelfes = self.get_shelf_names()
        num_shelfes = len(all_shelfes)

        current_pos = all_shelfes.index(shelf_name) + 1
        if relative:
            pos = num_shelfes + pos
        pos = max(1, min(pos, num_shelfes))
        pc.shelfTabLayout(self.name, e=True, moveTab=[current_pos, pos])

    def shelf_mel_to_dict(self, shelf_name):
        shelf_dict = {"name": shelf_name, "buttons": []}
        with open(os.path.join(self.shelf_dir, "shelf_{}.mel".format(shelf_name))) as shelf_file:
            shelf_code_lines = shelf_file.readlines()
          
        flags = defaultdict(list)
        typ = None

        for line in shelf_code_lines:
            line = line.lstrip().rstrip()
            
            if line.startswith("shelfButton"):
                shelf_dict["buttons"].append({})
                typ = "button"
                continue
            elif line.startswith("separator"):
                shelf_dict["buttons"].append({"type": "separator"})
                typ = "separator"
                continue
                
            if line.startswith("-") and typ=="button":
                first_blank = line.index(" ")
                flag_name = line[1:first_blank]
                str_value =  line[first_blank + 1:]
                try:
                    val = ast.literal_eval(str_value)
                except SyntaxError:
                    val = [ast.literal_eval(v) for v in str_value.split()]
                shelf_dict["buttons"][-1][flag_name] = val
                flags[flag_name].append(val)
            
        relevant_flags = [k for k in flags if not all_the_same(flags[k])]
        relevant_flags.append("type")
        shelf_dict["buttons"] = [
            keep_keys(b, relevant_flags) for b in shelf_dict["buttons"]
        ]

        return shelf_dict

    def set_flags_for_all_buttons(self, shelf_name, flags):
        for button in self.get_button_names(shelf_name):
            try:
                pc.shelfButton(button, edit=True, **flags)
            except RuntimeError:
                try:
                    pc.separator(button, edit=True, **flags)
                except TypeError:
                    pass

    def save_json(self, shelf_name, json_file, replace=False):
        self.save()
        shelf_dict = self.shelf_mel_to_dict(shelf_name)
        shelf_dict["replace"] = replace
        with open(json_file, "w+") as f:
            json.dump(
                shelf_dict, f, indent=4
            )

    def load_from_json(self, json_file: str, force=False):
        try:
            with open(json_file) as f:
                shelf = json.load(f) #  , object_hook=ascii_encode_dict)
        except (ValueError, IOError) as e:
            pc.warning("'{}' load error. Shelf not loaded/updated. ({})".format(
                json_file, e
            ))
            return

        if self.add_shelf(shelf["name"], replace=shelf["replace"] or force):
            for button in shelf["buttons"]:
                self.add_button(shelf["name"], button)

            self.move_tab(shelf["name"], shelf.get("position", 50))

            self.save()
