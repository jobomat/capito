"""Module for easy screenshot creation helpers."""
from pathlib import Path
from typing import Callable, Tuple

import maya.api.OpenMaya as om
import pymel.core as pc
from capito.maya.viewport.hud import HUDs


class Screenshooter:
    """Class providing a Screenshot "inbetween" window in your tool."""

    def __init__(
        self,
        viewport_size: Tuple[int, int] = (640, 400),
        resize: Tuple[int, int] = None,
        filepath: Path = Path(),
        file_format: str = "jpg",
        callback_on_accept: Callable[[Path], None] = None,
        kwargs_on_accept: dict = None,
        callback_on_abort: Callable[[], None] = None,
        kwargs_on_abort: dict = None,
        use_cam: pc.nodetypes.Transform = None,
        show_settings: bool = True,
        settings: dict=None
    ):
        self.vp_width = viewport_size[0]
        self.vp_height = viewport_size[1]
        if resize is not None:
            self.img_width = resize[0]
            self.img_height = resize[1]
        self.filepath = filepath if isinstance(filepath, Path) else Path(filepath)
        self.file_format = file_format
        self.cb_on_accept = callback_on_accept
        self.kwargs_on_accept = kwargs_on_accept or {}
        self.cb_on_abort = callback_on_abort
        self.kwargs_on_abort = kwargs_on_abort or {}
        self.delete_cam_on_cleanup = False if use_cam else True
        sel = pc.selected()
        if use_cam:
            self.cam = use_cam
            self.cam_shape = self.cam.getShape()
        else:
            self.cam, self.cam_shape = pc.camera()
            self.cam.setRotation((-30, 45, 0))
        pc.select(sel)
        self.show_settings = show_settings
        self.settings = self._get_std_settings() if settings is None else settings

        self.state_string = ""
        self.huds = HUDs()

        self.gui()
        self.setup_viewport()

    def gui(self):
        """Build the window"""
        with pc.window(
            title="Screenshooter",
            w=self.vp_width, 
            h=self.vp_height + 30,
            cc=pc.Callback(self.cleanup)
        ) as self.win:
            with pc.formLayout() as form_layout:
                self.viewport = pc.modelEditor(camera=self.cam)
                with pc.rowLayout(
                    nc=3 if self.show_settings else 2,
                    h=30,
                    adj=2 if self.show_settings else 1,
                ) as row_layout:
                    if self.show_settings:
                        pc.button("Settings")
                    pc.button("Accept", c=pc.Callback(self.capture))
                    pc.button("Cancel", c=pc.Callback(self.abort))

        form_layout.attachForm(self.viewport, "top", 0)
        form_layout.attachForm(self.viewport, "right", 0)
        form_layout.attachForm(self.viewport, "left", 0)
        form_layout.attachForm(row_layout, "right", 0)
        form_layout.attachForm(row_layout, "bottom", 0)
        form_layout.attachForm(row_layout, "left", 0)
        form_layout.attachControl(self.viewport, "bottom", 0, row_layout)

    def setup_viewport(self):
        """Function called before showing gui to set specific viewport options."""
        self.state_string = self.viewport.getStateString()
        for setting, value in self.settings.items():
            getattr(self.viewport, setting)(value)

        self.huds.hide_all()

        pc.SCENE.hardwareRenderingGlobals.multiSampleEnable.set(1)

        pc.rendering.viewFit(self.cam_shape, all=True)

    def _get_std_settings(self):
        return {
            "setLineWidth": 2,
            "setWireframeOnShaded": 0,
            "setDisplayTextures": 1,
            "setGrid": 0,
            "setDisplayAppearance": "smoothShaded"
        }

    def _list_viewport_settings(self):
        print("\n".join(dir(type(self.viewport))))

    def reset_viewport(self):
        """Perform the opposite actions of 'setup_viewport' to reset the viewport."""
        pc.mel.eval(
            self.state_string.replace(self.cam.name(long=True), "|persp").replace(
                "$editorName", "modelPanel4"
            )
        )

        self.huds.recall_current()

        pc.SCENE.hardwareRenderingGlobals.multiSampleEnable.set(0)

    def cleanup(self, close_button_pressed=False):
        """Clean up every generated objects and close window if necessary."""
        self.reset_viewport()
        if self.delete_cam_on_cleanup:
            pc.delete(self.cam)

    def abort(self):
        """Action performed on user press 'Abort'."""
        if self.cb_on_abort is not None:
            self.cb_on_abort(**self.kwargs_on_abort)
        pc.deleteUI(self.win)

    def capture(self):
        """Action performed on user press 'Accept'."""
        self.viewport.setActiveView(True)
        pc.refresh(currentView=True, fn=str(self.filepath), fe=self.file_format)

        img = om.MImage()
        img.readFromFile(str(self.filepath))
        img.resize(200, 200, True)
        img.writeToFile(str(self.filepath), self.file_format)
        if self.cb_on_accept is not None:
            self.cb_on_accept(**self.kwargs_on_accept)
        pc.deleteUI(self.win)


# Screenshooter(show_settings=False)
