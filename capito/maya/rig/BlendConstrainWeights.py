import pymel.core as pc


class BlendConstrainWeights():
    def __init__(self):
        self.script_jobs = []
        self.main_padding = 3
        self.gui()

    def gui(self):
        win_id = "blend_constrain_window"
        window_width = 400
        window_height = 255

        if pc.window(win_id, q=1, exists=1):
            pc.deleteUI(win_id)

        with pc.window(win_id, title="Blend [x = 1 - y]", wh=[window_width, window_height]) as self.win:
            with pc.formLayout(numberOfDivisions=100) as self.main_fl:
                with pc.columnLayout(adj=True) as self.top_bar:
                    with pc.horizontalLayout():
                        with pc.columnLayout(adj=True, rs=5):
                            pc.button(label="Load Driver Node",
                                      c=self.load_driver)
                            self.driver_text = pc.text(
                                label="Select Driver Attribute:", align="left")
                        with pc.columnLayout(adj=True, rs=5):
                            pc.button(label="Load Driven Node",
                                      c=self.load_driven)
                            self.driven_text = pc.text(
                                label="Select Driven Attribute:", align="left")
                with pc.horizontalLayout() as self.content_hl:
                    self.driver_scrollList = pc.textScrollList()
                    self.driven_scrollList = pc.textScrollList(
                        allowMultiSelection=True)
                with pc.horizontalLayout() as self.bottom_bar:
                    pc.button(label="Create Blend or Switch Channels",
                              c=self.create_setup)

        self.main_fl.attachForm(self.top_bar, "top", self.main_padding)
        self.main_fl.attachForm(self.top_bar, "left", self.main_padding)
        self.main_fl.attachForm(self.top_bar, "right", self.main_padding)

        self.main_fl.attachForm(self.content_hl, "left", self.main_padding)
        self.main_fl.attachForm(self.content_hl, "right", self.main_padding)

        self.main_fl.attachForm(self.bottom_bar, "left", self.main_padding)
        self.main_fl.attachForm(self.bottom_bar, "right", self.main_padding)
        self.main_fl.attachForm(self.bottom_bar, "bottom", self.main_padding)

        self.main_fl.attachControl(
            self.content_hl, "top", 0, self.top_bar
        )
        self.main_fl.attachControl(
            self.content_hl, "bottom", self.main_padding, self.bottom_bar
        )
        self.main_fl.attachNone(self.top_bar, "bottom")
        self.main_fl.attachNone(self.bottom_bar, "top")

    def load_driver(self, *args):
        self.driver_scrollList.removeAll()
        self.driver = pc.selected()[0]
        self.driver_text.setLabel(self.driver.name())
        self.driver_scrollList.append(
            [a.name().split(".")[1]
             for a in self.driver.listAttr(keyable=True)]
        )

    def load_driven(self, *args):
        self.driven_scrollList.removeAll()
        self.driven = pc.selected()[0]
        self.driven_text.setLabel(self.driven.name())
        self.driven_scrollList.append(
            [a.name().split(".")[1]
             for a in self.driven.listAttr(keyable=True)]
        )

    def create_setup(self, *args):
        driver_attrs = self.driver_scrollList.getSelectItem()
        driven_attrs = self.driven_scrollList.getSelectItem()

        if len(driver_attrs) != 1:
            pc.confirmDialog(title="Specify Driver Attribute",
                             message='Please select a driver attributes.', button=["OK"])
            return

        driver_attr = self.driver.attr(driver_attrs[0])

        if len(driven_attrs) != 2:
            pc.confirmDialog(title="Wrong Number of Driven Attibutes",
                             message='Please select exactly 2 driven attributes.', button=["OK"])
            return

        driven_1 = self.driven.attr(driven_attrs[0])
        driven_2 = self.driven.attr(driven_attrs[1])

        direct_driven = driven_1
        reverse_driven = driven_2
        reverse_node = None

        if driven_1.listConnections(destination=False) and driven_2.listConnections(destination=False):
            print driven_1.listConnections(destination=False), driven_2.listConnections(destination=False)
            if driven_1.listConnections(type="reverse"):
                reverse_node = driven_1.listConnections(
                    type="reverse", destination=False)[0]
            elif driven_2.listConnections(type="reverse"):
                reverse_node = driven_2.listConnections(
                    type="reverse", destination=False)[0]
                direct_driven = driven_2
                reverse_driven = driven_1
            else:
                pc.warning(
                    "Initial connections not set up by this script... Aborted.")
                return
        else:
            reverse_node = pc.createNode("reverse")
            driver_attr >> reverse_node.attr("inputX")

        driver_attr >> direct_driven
        reverse_node.attr("outputX") >> reverse_driven


if __name__ == "__main__":
    BlendConstrainWeights()
