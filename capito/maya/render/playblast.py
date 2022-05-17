from pathlib import Path
import os

import pymel.core as pc

from capito.maya.ui.widgets import file_chooser_button
from capito.maya.env.vars import FRAME_RATE_MAP
from capito.maya.env.settings import SettingsManagerMixin
from capito.maya.util.process import SubQ
from capito.maya.render.processes import (
    Ffmpeg,
    BatchRender,
    HW2PreRenderMel,
    RenderFlag,
)


RENDERER_MAP = {"Hardware 2.0": "hw2", "Arnold": "arnold"}


def remap_value(value, OldMin, OldMax, NewMin, NewMax):
    return (((value - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin


class BackgroundPlayblast(SettingsManagerMixin):
    def __init__(self):
        self.window_name = "bg_playblast_win"
        self.burnin_cols = {"left": None, "center": None, "right": None}
        self.init_settings()
        self.gui()
        default_preset = self.settings.get("default_preset", "CA Stupro")
        self.set_drawtext_preset(self.settings.burnin_presets[default_preset])
        self.set_drawtext_menu_option(default_preset)

    def gui(self):
        default_resolution = pc.PyNode("defaultResolution")
        # default_render_globals = pc.PyNode("defaultRenderGlobals")

        padding = 5

        if pc.window(self.window_name, exists=True):
            pc.deleteUI(self.window_name)
        with pc.window(self.window_name, title="Background Playblast"):
            with pc.formLayout(numberOfDivisions=100) as main_fl:
                with pc.columnLayout(adj=True, rs=padding) as self.main_cl:
                    self.scene_tfg = file_chooser_button(
                        "Scene",
                        1,
                        " Choose... ",
                        text=pc.system.sceneName(),
                        okCaption="Choose",
                        tfb_kwargs={"cw3": (60, 100, 50)},
                    )
                    with pc.popupMenu(parent=self.scene_tfg):
                        pc.menuItem("Current Scene", c=self.set_scene_to_current_scene)
                    pc.separator(h=2)
                    self.renderdir_tfg = file_chooser_button(
                        "Render Dir",
                        3,
                        " Choose... ",
                        text=self.get_current_image_dir(),
                        okCaption="Set",
                        tfb_kwargs={"cw3": (60, 100, 50)},
                    )
                    with pc.popupMenu(parent=self.renderdir_tfg):
                        pc.menuItem(
                            "Current Project Image Dir",
                            c=pc.Callback(self.set_renderdir_to_current_imagedir),
                        )
                    pc.separator(h=2)
                    with pc.rowLayout(nc=5, cw=(2, 30), adj=2, cat=(2, "right", 4)):
                        with pc.optionMenuGrp(
                            label="Camera", cw=(1, 60), adj=2, cal=(1, "left")
                        ) as self.camera_optionMenuGrp:
                            for cam in pc.ls(type="camera"):
                                if cam.renderable.get():
                                    pc.menuItem(cam.getParent().name())

                        self.image_name_textFieldGrp = pc.textFieldGrp(
                            label="Image Name",
                            cw=(1, 75),
                            adj=2,
                            cal=(1, "right"),
                            text=self.get_current_scene_name(),
                        )
                        with pc.popupMenu(parent=self.image_name_textFieldGrp):
                            pc.menuItem(
                                "Current Scene Name",
                                c=pc.Callback(
                                    self.set_image_name_to_current_scene_name
                                ),
                            )
                        pc.text(label="Pad")
                        self.padding_intField = pc.intField(value=4, w=20)
                        with pc.optionMenuGrp(
                            label="File Format", cw=(1, 77), cat=(1, "left", 10)
                        ) as self.file_format_optionMenuGrp:
                            pc.menuItem("png")
                            pc.menuItem("jpg")
                            pc.menuItem("exr")

                    pc.separator(h=2)
                    with pc.rowLayout(nc=8, adj=1):
                        with pc.optionMenuGrp(
                            label="Renderer",
                            cc=self.build_render_settings,
                            cw=(1, 60),
                            adj=2,
                            cal=(1, "left"),
                        ) as self.renderer_optionMenuGrp:
                            for renderer in RENDERER_MAP:
                                pc.menuItem(renderer)
                        pc.text(label="Start", w=35)
                        self.start_intField = pc.intField(
                            value=pc.playbackOptions(q=1, min=1), w=40
                        )
                        pc.text(label="End", w=35)
                        self.end_intField = pc.intField(
                            value=pc.playbackOptions(q=1, max=1), w=40
                        )
                        pc.text(label="Step", w=35)
                        self.step_intField = pc.intField(value=1, w=20)
                        self.resolution_intFieldGrp = pc.intFieldGrp(
                            label="W | H",
                            numberOfFields=2,
                            cw3=(40, 50, 50),
                            value1=default_resolution.width.get(),
                            value2=default_resolution.height.get(),
                        )
                    pc.separator(h=1, style="none")
                    with pc.frameLayout(
                        label="Hardware 2.0 Render Settings",
                        bgc=(0.09, 0.16, 0.29),
                        mh=4,
                        mw=4,
                        collapsable=True,
                    ) as self.renderer_fl:
                        self.build_hw2_rendersettings()
                    pc.separator(h=1, style="none")
                    with pc.frameLayout(
                        label="FFMPEG Encoding Settings",
                        bgc=(0.07, 0.22, 0.25),
                        mh=4,
                        mw=4,
                        collapsable=True,
                    ):
                        with pc.columnLayout(adj=True):
                            self.mp4_tfg = file_chooser_button(
                                "MP4 File",
                                0,
                                " Save as... ",
                                text=f"{self.get_current_image_dir()}/{self.get_current_scene_name()}.mp4",
                                okCaption="Choose",
                                tfb_kwargs={"cw3": (60, 100, 50)},
                            )
                            with pc.rowLayout(nc=4, adj=4):
                                pc.text(label="Framerate", align="left", w=60)
                                self.fps_intField = pc.intField(
                                    value=self.get_fps(), w=30
                                )
                                with pc.popupMenu(parent=self.fps_intField):
                                    pc.menuItem(
                                        "From project Settings",
                                        c=pc.Callback(self.set_fps),
                                    )
                                self.quality_intSliderGrp = pc.intSliderGrp(
                                    label="Quality",
                                    v=65,
                                    min=0,
                                    max=100,
                                    cw3=(50, 30, 100),
                                    f=True,
                                )
                                self.ffmpeg_exe_tfg = file_chooser_button(
                                    "FFMPEG exe",
                                    1,
                                    "...",
                                    text=self.get_ffmpeg_exe(),
                                    okCaption="Choose",
                                    tfb_kwargs={
                                        "cw3": (75, 100, 50),
                                        "cat": (1, "right", 0),
                                    },
                                )
                    pc.separator(h=1, style="none")
                    with pc.frameLayout(
                        label="Burn Ins",
                        bgc=(0.284, 0.18, 0.07),
                        mh=4,
                        mw=4,
                        collapsable=True,
                    ):
                        with pc.columnLayout(adj=True):
                            with pc.rowLayout(
                                nc=3, ct3=("left", "left", "left"), co3=(0, 0, 4)
                            ):
                                with pc.optionMenuGrp(
                                    label="Presets",
                                    cw=(1, 60),
                                    cal=(1, "left"),
                                    cc=self.change_drawtext,
                                ) as self.burnin_presets_MenuGrp:
                                    for item in self.settings.burnin_presets.keys():
                                        pc.menuItem(item)
                                pc.button(
                                    label="Save New Preset", c=self.save_drawtext_preset
                                )
                                pc.button(
                                    label="Use as Default Preset",
                                    c=self.save_default_preset,
                                )
                            with pc.horizontalLayout():
                                with pc.columnLayout(adj=True):
                                    pc.text(
                                        label="LEFT",
                                        align="center",
                                        h=20,
                                        font="boldLabelFont",
                                    )
                                    add_left_btn = pc.button(label="Add Line")
                                    with pc.columnLayout(adj=True) as self.burnin_cols[
                                        "left"
                                    ]:
                                        pass
                                with pc.columnLayout(adj=True):
                                    pc.text(
                                        label="CENTER",
                                        align="center",
                                        h=20,
                                        font="boldLabelFont",
                                    )
                                    add_center_btn = pc.button(label="Add Line")
                                    with pc.columnLayout(adj=True) as self.burnin_cols[
                                        "center"
                                    ]:
                                        pass
                                with pc.columnLayout(adj=True):
                                    pc.text(
                                        label="RIGHT",
                                        align="center",
                                        h=20,
                                        font="boldLabelFont",
                                    )
                                    add_right_btn = pc.button(label="Add Line")
                                    with pc.columnLayout(adj=True) as self.burnin_cols[
                                        "right"
                                    ]:
                                        pass
                                add_left_btn.setCommand(
                                    pc.Callback(
                                        self.add_drawtext, self.burnin_cols["left"]
                                    )
                                )
                                add_center_btn.setCommand(
                                    pc.Callback(
                                        self.add_drawtext, self.burnin_cols["center"]
                                    )
                                )
                                add_right_btn.setCommand(
                                    pc.Callback(
                                        self.add_drawtext, self.burnin_cols["right"]
                                    )
                                )
                    with pc.popupMenu(parent=self.resolution_intFieldGrp):
                        pc.menuItem(
                            "From Render Settings",
                            c=pc.Callback(self.set_resolution_from_rendersettings),
                        )
                        pc.menuItem("50%", c=pc.Callback(self.set_half_resolution))
                    pc.separator(h=2)
                with pc.horizontalLayout(ratios=(1, 1, 2)) as button_hl:
                    pc.button(
                        label="Render",
                        c=pc.Callback(self.run, ["render"]),
                        bgc=(0.09, 0.16, 0.29),
                    )
                    pc.button(
                        label="Encode",
                        c=pc.Callback(self.run, ["encode"]),
                        bgc=(0.07, 0.22, 0.25),
                    )
                    pc.button(
                        label="Render + Encode",
                        c=pc.Callback(self.run, ["render", "encode"]),
                        bgc=(0.5, 0.5, 0.5),
                    )
                    # pc.button(label="Close")

        main_fl.attachForm(self.main_cl, "top", padding)
        main_fl.attachForm(self.main_cl, "left", padding)
        main_fl.attachForm(self.main_cl, "right", padding)
        main_fl.attachForm(button_hl, "bottom", padding)
        main_fl.attachForm(button_hl, "left", padding)
        main_fl.attachForm(button_hl, "right", padding)

    def set_scene_to_current_scene(self, *args):
        self.scene_tfg.setText(pc.system.sceneName())

    def get_current_image_dir(self):
        image_dir = Path(pc.workspace.path) / pc.workspace.fileRules.get("images", "")
        return str(image_dir).replace("\\", "/")

    def set_renderdir_to_current_imagedir(self, *args):
        self.renderdir_tfg.setText(self.get_current_image_dir())

    def get_current_scene_name(self, extension=False):
        sn = Path(pc.system.sceneName())
        if not sn:
            return ""
        if extension:
            return sn.name
        return ".".join(sn.name.split(".")[:-1])

    def set_image_name_to_current_scene_name(self):
        self.image_name_textFieldGrp.setText(self.get_current_scene_name())

    def get_fps(self):
        key = pc.language.OptionVarDict()["workingUnitTime"]
        return FRAME_RATE_MAP[key]

    def set_fps(self):
        self.fps_intField.setValue(self.get_fps())

    def get_ffmpeg_exe(self):
        exe = os.environ.get("ffmpeg", "")
        return exe

    def get_quality(self):
        return int(remap_value(self.quality_intSliderGrp.getValue(), 0, 100, 63, 0))

    def set_resolution_from_rendersettings(self):
        default_resolution = pc.PyNode("defaultResolution")
        self.resolution_intFieldGrp.setValue1(default_resolution.width.get())
        self.resolution_intFieldGrp.setValue2(default_resolution.height.get())

    def set_half_resolution(self):
        self.resolution_intFieldGrp.setValue1(
            self.resolution_intFieldGrp.getValue1() * 0.5
        )
        self.resolution_intFieldGrp.setValue2(
            self.resolution_intFieldGrp.getValue2() * 0.5
        )

    def build_render_settings(self, renderer):
        if renderer == "Arnold":
            self.build_arnold_rendersettings()
        elif renderer == "Hardware 2.0":
            self.build_hw2_rendersettings()

    def build_hw2_rendersettings(self):
        self.renderer_fl.setLabel("Hardware 2.0 Render Settings")
        for child in self.renderer_fl.getChildren():
            pc.deleteUI(child)
        with pc.rowLayout(nc=3, parent=self.renderer_fl):
            self.hw2_aa_checkBox = pc.checkBox(value=True, label="Antialiasing")
            with pc.optionMenuGrp(
                label="AA Oversampling", cw=(1, 100)
            ) as self.hw2_oversampling_optionMenuGrp:
                pc.menuItem("2")
                pc.menuItem("4")
                pc.menuItem("8")
                pc.menuItem("16")
            self.hw2_oversampling_optionMenuGrp.setValue("16")
            self.hw2_ao_checkBox = pc.checkBox(
                value=False, label="SS Ambient Occlusion"
            )

    def build_arnold_rendersettings(self):
        self.renderer_fl.setLabel("Arnold Render Settings")

        self.arnold_samplingflags = [
            RenderFlag("-ai:as", 3, "Cam"),
            RenderFlag("-ai:hs", 1, "Diff"),
            RenderFlag("-ai:gs", 0, "Spec"),
            RenderFlag("-ai:rs", 0, "Trans"),
            RenderFlag("-ai:bssrdfs", 0, "SSS"),
        ]
        self.arnold_raydepthflags = [
            RenderFlag("-ai:td", 5, "Total"),
            RenderFlag("-ai:dif", 1, "Diff"),
            RenderFlag(" -ai:glo", 1, "Spec"),
            RenderFlag("-ai:rfr", 1, "Trans"),
        ]
        for child in self.renderer_fl.getChildren():
            pc.deleteUI(child)
        with pc.columnLayout(adj=True, parent=self.renderer_fl):
            with pc.rowLayout(nc=13, cw=(1, 60), adj=12, cat=(13, "right", 0)):
                pc.text(label="Sampling:", font="boldLabelFont")
                for f in self.arnold_samplingflags:
                    pc.text(label=f.label, w=35)
                    f.ui = pc.intField(value=f.value, w=25)
                pc.text(label="", w=5)
                self.arnold_threads_intFieldGrp = pc.intFieldGrp(
                    label="Threads", value1=7, cw2=(60, 30)
                )
            with pc.rowLayout(nc=11, cw=(1, 60), adj=10, cat=(11, "right", 0)):
                pc.text(label="Ray Depth:", font="boldLabelFont")
                for f in self.arnold_raydepthflags:
                    pc.text(label=f.label, w=35)
                    f.ui = pc.intField(value=f.value, w=25)
                pc.text(label="", w=5)
                self.arnold_lic_checkBox = pc.checkBox(
                    label="Skip License Check", value=False, w=120
                )

    def add_drawtext(self, col_layout, text=""):
        line = pc.textFieldButtonGrp(
            parent=col_layout, cw=(1, 125), bl="Del", adj=1, text=text
        )
        line.buttonCommand(pc.Callback(pc.deleteUI, line))
        with pc.popupMenu(parent=line):
            pc.menuItem("Frame Number", c=pc.Callback(line.setText, "<frame>"))
            pc.menuItem("Date/Time", c=pc.Callback(line.setText, "<datetime>"))
            pc.menuItem("Scene Name", c=pc.Callback(line.setText, "<scenename>"))
            pc.menuItem("Project Name", c=pc.Callback(line.setText, "<projectname>"))
            pc.menuItem("Camera Name", c=pc.Callback(line.setText, "<camera>"))

    def get_encode_cmd(self):
        ff = Ffmpeg(exe=self.ffmpeg_exe_tfg.getText())

        ff.box_opacity = 0.5

        img_path = self.renderdir_tfg.getText()
        img_name = self.image_name_textFieldGrp.getText()
        img_pad = self.padding_intField.getValue()
        img_ext = self.file_format_optionMenuGrp.getValue()
        ff.input = f"{img_path}/{img_name}.%0{img_pad}d.{img_ext}"

        ff.output = self.mp4_tfg.getText()
        ff.quality = self.get_quality()
        ff.framerate = self.fps_intField.getValue()

        for line in self.burnin_cols["left"].getChildren():
            t = self.preprocess_drawtext(line.getChildren()[0].getText())
            ff.text["left"].append(t)
        for line in self.burnin_cols["center"].getChildren():
            t = self.preprocess_drawtext(line.getChildren()[0].getText())
            ff.text["center"].append(t)
        for line in self.burnin_cols["right"].getChildren():
            t = self.preprocess_drawtext(line.getChildren()[0].getText())
            ff.text["right"].append(t)

        return ff.cmd()

    def preprocess_drawtext(self, t):
        replace_map = {
            "<scenename>": self.get_current_scene_name(extension=True),
            "<projectname>": Path(pc.workspace.name).name,
            "<camera>": self.camera_optionMenuGrp.getValue(),
        }
        for s, r in replace_map.items():
            t = t.replace(s, r)
        return t

    def set_drawtext_preset(self, drawtext_dict=None):
        for col in self.burnin_cols.values():
            for child in col.getChildren():
                pc.deleteUI(child)
        for col, values in drawtext_dict.items():
            for text in values:
                self.add_drawtext(self.burnin_cols[col], text)

    def change_drawtext(self, preset_name):
        self.set_drawtext_preset(self.settings.burnin_presets[preset_name])

    def save_drawtext_preset(self, *args):
        result = pc.promptDialog(
            title="Save Preset",
            text="New Burn In Preset",
            message="Enter Name:",
            button=["OK", "Cancel"],
            defaultButton="OK",
            cancelButton="Cancel",
            dismissString="Cancel",
        )
        if result != "OK":
            return
        preset_name = pc.promptDialog(query=True, text=True)

        preset = {}
        for key, col in self.burnin_cols.items():
            preset[key] = []
            for line in col.getChildren():
                preset[key].append(line.getChildren()[0].getText())

        self.settings.burnin_presets[preset_name] = preset
        self.settings.save()

        self.burnin_presets_MenuGrp.getChildren()[1].addMenuItems([preset_name])
        self.set_drawtext_menu_option(preset_name)

    def save_default_preset(self, *args):
        self.settings.default_preset = self.burnin_presets_MenuGrp.getChildren()[
            1
        ].getValue()
        self.settings.save()

    def set_drawtext_menu_option(self, value):
        self.burnin_presets_MenuGrp.getChildren()[1].setValue(value)

    def run(self, actions):
        sq = SubQ()
        if "render" in actions:
            sq.add(self.get_render_cmd())
            sq.add_message("Rendering finished.")
        if "encode" in actions:
            if not self.ffmpeg_exe_tfg.getText():
                pc.confirmDialog(
                    title="Info missing",
                    message="Please specify where to find 'ffmpeg.exe'.",
                )
            else:
                sq.add(self.get_encode_cmd())
                sq.add_message("Encoding finished.")
        if sq.length():
            sq.run()

    def get_render_cmd(self):
        renderer = RENDERER_MAP[self.renderer_optionMenuGrp.getValue()]

        br = BatchRender(
            scene=self.scene_tfg.getText(),
            rd=self.renderdir_tfg.getText(),
            image_name=self.image_name_textFieldGrp.getText(),
            s=self.start_intField.getValue(),
            e=self.end_intField.getValue(),
            b=self.step_intField.getValue(),
            x=self.resolution_intFieldGrp.getValue1(),
            y=self.resolution_intFieldGrp.getValue2(),
            r=renderer,
            p=self.padding_intField.getValue(),
            cam=self.camera_optionMenuGrp.getValue(),
            of=self.file_format_optionMenuGrp.getValue(),
        )

        if renderer == "hw2":
            hw2mel = HW2PreRenderMel(
                aa_enable=1 if self.hw2_aa_checkBox.getValue() else 0,
                aa_samples=self.hw2_oversampling_optionMenuGrp.getValue(),
                ao_enable=1 if self.hw2_ao_checkBox.getValue() else 0,
            )
            br.flags.append(RenderFlag("-preRender", hw2mel.get_mel(), "Pre Render"))
        elif renderer == "arnold":
            for flag in self.arnold_raydepthflags + self.arnold_samplingflags:
                flag.value = flag.ui.getValue()
                br.flags.append(flag)
            br.flags.append(
                RenderFlag(
                    "-ai:threads", self.arnold_threads_intFieldGrp.getValue1(), ""
                )
            )
            br.flags.append(
                RenderFlag(
                    "-ai:slc", 1 if self.arnold_lic_checkBox.getValue() else 0, ""
                )
            )

        return br.cmd()


# BackgroundPlayblast()
