# coding: utf-8
import sys
import types
import pymel.core as pc
import webbrowser

HELP_ROOT_URL = 'http://help.autodesk.com/cloudhelp/2022/ENU/Maya-Tech-Docs/PyMel/'


def syspath():
    print('sys.path:')
    for p in sys.path:
        print(f'  {p}')


def info(obj):
    """Prints information about the object."""

    lines = ['Info for %s' % obj.name(),
             'Attributes:']
    # Get the name of all attributes
    for a in obj.listAttr():
        lines.append('  ' + a.name())
    lines.append('MEL type: %s' % obj.type())
    lines.append('MRO:')
    lines.extend(['  ' + t.__name__ for t in type(obj).__mro__])
    result = '\n'.join(lines)
    print(result)


def _is_pymel(obj):
    try:
        module = obj.__module__
    except AttributeError:
        try:
            module = obj.__name__
        except AttributeError:
            return None
    return module.startswith('pymel')


def _py_to_helpstr(obj):
    # if isinstance(obj, str):
    #     return 'search.html?q={}'.format(obj.replace(' ', '+'))
    if not _is_pymel(obj):
        return None
    if isinstance(obj, types.ModuleType):
        return 'generated/{mod}.html#module-{mod}'.format(
            mod=obj.__name__
        )
    if isinstance(obj, types.MethodType):
        return ('generated/classes/{mod}/'
                '{mod}.{typ}.html'
                '#{mod}.{typ}.{met}'.format(
                    mod=obj.__module__,
                    typ=obj.im_class.__name__,
                    met=obj.__name__))
    if isinstance(obj, types.FunctionType):
        return ('generated/functions/{mod}/'
                '{mod}.{func}.html'
                '#{mod}.{func}'.format(
                    mod=obj.__module__,
                    func=obj.__name__))
    if not isinstance(obj, type):
        obj = type(obj)
    return ('generated/classes/{mod}/'
            '{mod}.{typ}.html'
            '#{mod}.{typ}'.format(
                mod=obj.__module__,
                typ=obj.__name__))


def pmhelp(obj):
    """Gives help for a pymel or python object.

    If obj is not a PyMEL object, use Python's built-in
    `help` function.
    If obj is a string, open a web browser to a search in the
    PyMEL help for the string.
    Otherwise, open a web browser to the page for the object.
    """
    tail = _py_to_helpstr(obj)
    if tail is None:
        help(obj)
    else:
        webbrowser.open(HELP_ROOT_URL + tail)


class AttributeFinder():
    def __init__(self):
        self.nodes = {}
        self.gui()

    def __call__(self):
        self.gui()
        pass

    def get_node_state(self, node):
        node_state = {}
        for attr in node.listAttr():
            if len(attr.name().split(".")) > 2:
                print(attr.name())
                continue
            try:
                value = attr.get()
                node_state[attr] = value
                print(attr, value)
            except:
                node_state[attr] = "Unsure"
        return node_state

    def add_nodes(self):
        nodes = pc.selected()
        for node in nodes:
            self.nodes[node.name()] = self.get_node_state(node)

    def diff(self):
        differences = {}
        for nodename, saved_state in self.nodes.items():
            differences[nodename] = []
            for attr, value in saved_state.items():
                try:
                    new_value = attr.get()
                except:
                    new_value = "Compound"
                if value != new_value:
                    differences[nodename].append({
                        "attr": attr.name(),
                        "old_value": str(value),
                        "new_value": str(new_value)
                    })
        return differences

    def ascii_diff(self):
        differences = self.diff()
        cols = [50, 20, 20]
        headers = ["Attribute", "old_value", "changed to"]
        self.logtext = ""

        for node, changed in differences.items():
            self.log("\n")
            self.log("-" * sum(cols))
            self.log(node.center(sum(cols)))
            self.log("-" * sum(cols))
            self.log(
                "{header1}{header2}{header3}".format(
                    header1=headers[0].ljust(cols[0]),
                    header2=headers[1].ljust(cols[1]),
                    header3=headers[2].ljust(cols[2])
                )
            )
            self.log("-" * sum(cols))
            for change in changed:
                self.log(
                    "{attr}{old_value}{new_value}".format(
                        attr=change["attr"].ljust(cols[0]),
                        old_value=change["old_value"].ljust(cols[1]),
                        new_value=change["new_value"].ljust(cols[2]),
                    )
                )
        return self.logtext

    def log(self, value):
        self.logtext = "{}{}\n".format(self.logtext, str(value))

    def gui(self):
        self.win_id = "attribute_finder_win"
        margin = 10

        if pc.window(self.win_id, q=1, exists=1):
            pc.deleteUI(self.win_id)

        with pc.window(self.win_id, title="Attribute Finder", wh=[420, 400]) as win:
            with pc.frameLayout(borderVisible=True, labelVisible=False,
                                marginWidth=margin, marginHeight=margin):
                with pc.columnLayout(adj=True):
                    pc.button(label="Add Selected", c=self.gui_add_nodes)
                    self.scan_button = pc.button(
                        label="Scan for Changes", c=self.gui_diff, enable=False
                    )
                    pc.text(label=" ")
                    self.list_columnLayout = pc.columnLayout(adj=True)

    def gui_add_nodes(self, *args):
        self.add_nodes()
        self.gui_diff()

    def gui_remove_node(self, node):
        del self.nodes[node]
        self.gui_diff()

    def gui_diff(self, *args):
        cw3 = [240, 90, 90]
        colors = ((0.28, 0.28, 0.28), (0.32, 0.32, 0.32))
        for child in self.list_columnLayout.getChildren():
            pc.deleteUI(child)

        differences = self.diff()
        for node, changed in differences.items():
            with pc.rowLayout(parent=self.list_columnLayout, bgc=[0.2, 0.2, 0.2],
                              nc=2, cw2=[150, 150], adj=1):
                pc.text(label=node, font="boldLabelFont", align="left")
                pc.button(
                    label="Remove".format(node), bgc=[0.4, 0.4, 0.4],
                    c=pc.Callback(self.gui_remove_node, node)
                )
            if len(changed):
                with pc.rowLayout(cal=[1, "left"], nc=3, cw3=cw3, adj=1, h=30,
                                  parent=self.list_columnLayout, bgc=[0.25, 0.25, 0.25]):
                    pc.text(label="Attribute", font="boldLabelFont")
                    pc.text(label="Old Value", font="boldLabelFont")
                    pc.text(label="New Value", font="boldLabelFont")
                for i, change in enumerate(changed):
                    with pc.rowLayout(cal=[1, "left"], nc=3, cw3=cw3, adj=1, h=30,
                                      parent=self.list_columnLayout, bgc=colors[i % 2]):
                        pc.text(label=change["attr"], font="boldLabelFont")
                        pc.text(label=change["old_value"])
                        pc.text(label=change["new_value"])
            else:
                pc.text(
                    label="No changes detected. Change some Values and click 'Scan for Changes'.",
                    parent=self.list_columnLayout, h=30, align="left"
                )
            pc.separator(parent=self.list_columnLayout, h=20)

        if len(self.nodes):
            self.scan_button.setEnable(True)
        else:
            self.scan_button.setEnable(False)
