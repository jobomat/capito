from pymel.all import optionVar, mel


hud_types = {
    "animationDetailsVisibility": "setAnimationDetailsVisibility",
    "cameraNamesVisibility": "setCameraNamesVisibility",
    "capsLockVisibility": "setCapsLockVisibility",
    "currentContainerVisibility": "setCurrentContainerVisibility",
    "currentFrameVisibility": "setCurrentFrameVisibility",
    "focalLengthVisibility": "setFocalLengthVisibility",
    "frameRateVisibility": "setFrameRateVisibility",
    "hikDetailsVisibility": "setHikDetailsVisibility",
    "objectDetailsVisibility": "setObjectDetailsVisibility",
    "particleCountVisibility": "setParticleCountVisibility",
    "polyCountVisibility": "setPolyCountVisibility",
    "sceneTimecodeVisibility": "setSceneTimecodeVisibility",
    "selectDetailsVisibility": "setSelectDetailsVisibility",
    "symmetryVisibility": "setSymmetryVisibility",
    "viewAxisVisibility": "setViewAxisVisibility",
    "viewportRendererVisibility": "setViewportRendererVisibility",
    "xgenHUDVisibility": "setXGenHUDVisibility"
}


def get_hud_state():
    return {ov: optionVar[ov] for ov in hud_types}


def set_hud_state(state_dict):
    for ov_name, mel_cmd in hud_types.items():
        mel.eval("{}({});".format(mel_cmd, state_dict[ov_name]))
