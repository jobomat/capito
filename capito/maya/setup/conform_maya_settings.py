"""Setup Maya conforming to Capito CONFIG."""
import pymel.core as pc
from capito.conf.config import CONFIG


def set_capito_project_settings():
    """Will conform the Maya settings to current Capito project CONFIG."""
    # Set the project:
    pc.workspace.open(CONFIG.CAPITO_PROJECT_DIR)
    # Set the framerate:
    pc.currentUnit(time=f"{CONFIG.FRAMERATE}fps")
    # Set the default plaback ranges:
    pc.playbackOptions(
        min=CONFIG.DEFAULT_STARTFRAME,
        max=CONFIG.DEFAULT_ENDFRAME,
        animationStartTime=CONFIG.DEFAULT_STARTFRAME,
        animationEndTime=CONFIG.DEFAULT_ENDFRAME,
    )
    # Set the timeslider to the first frame:
    pc.currentTime(CONFIG.DEFAULT_STARTFRAME)
    # Set the render resolution:
    pc.PyNode("defaultResolution").width.set(CONFIG.RESOLUTION_3D_X)
    pc.PyNode("defaultResolution").height.set(CONFIG.RESOLUTION_3D_Y)


set_capito_project_settings()
