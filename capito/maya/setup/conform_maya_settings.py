"""Setup Maya conforming to Capito CONFIG."""
import pymel.core as pc
from capito.conf.config import CONFIG


def set_capito_project_settings():
    """Will conform the Maya settings to current Capito project CONFIG."""
    # Set the project:
    if CONFIG.CAPITO_PROJECT_DIR:
        pc.workspace.open(CONFIG.CAPITO_PROJECT_DIR)
    else:
        pc.warning("Project not set. Attribute CONFIG.CAPITO_PROJECT_DIR missing.")
    # Set the framerate:
    if CONFIG.FRAMERATE:
        pc.currentUnit(time=f"{CONFIG.FRAMERATE}fps")
    else:
        pc.warning("Framerate not set. Attribute CONFIG.FRAMERATE missing.")
    # Set the default plaback ranges:
    if CONFIG.DEFAULT_STARTFRAME and CONFIG.DEFAULT_ENDFRAME:
        pc.playbackOptions(
            min=CONFIG.DEFAULT_STARTFRAME,
            max=CONFIG.DEFAULT_ENDFRAME,
            animationStartTime=CONFIG.DEFAULT_STARTFRAME,
            animationEndTime=CONFIG.DEFAULT_ENDFRAME,
        )
        # Set the timeslider to the first frame:
        pc.currentTime(CONFIG.DEFAULT_STARTFRAME)
    else:
        pc.warning("Startframe not set. Attribute CONFIG.STARTFRAME missing.")
        pc.warning("Endframe not set. Attribute CONFIG.ENDFRAME missing.")
    # Set the render resolution:
    if CONFIG.RESOLUTION_3D_X:
        pc.PyNode("defaultResolution").width.set(CONFIG.RESOLUTION_3D_X)
    else:
        pc.warning("Render resolution X not set. Attribute CONFIG.RESOLUTION_3D_X missing.")

    if CONFIG.RESOLUTION_3D_Y:
        pc.PyNode("defaultResolution").height.set(CONFIG.RESOLUTION_3D_Y)
    else:
        pc.warning("Render resolution Y not set. Attribute CONFIG.RESOLUTION_3D_Y missing.")

set_capito_project_settings()
