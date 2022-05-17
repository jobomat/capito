import pymel.core as pc


def add_toolbox_button(*args, **kwargs):
    """
    Use the kwargs of a maya textIconButton.
    For Example:
        command = The Function to call
        image = The Icon of Button
        label = The Label of Button
        style = "iconOnly", "textOnly", "iconAndTextHorizontal",
                "iconAndTextVertical", and "iconAndTextCentered". 
                (Note: "iconAndTextCentered" is only available on Windows).
                If "iconOnly" is set, the icon will be scaled to the size of the control.
    """
    kwargs["parent"] = pc.language.getMelGlobal('string', 'gToolBox')
    # tool_box_button_names = pc.flowLayout(gToolBox, q=True, childArray=True)
    return pc.iconTextButton(**kwargs)


def get_main_window_center():
    """Get center x,y screen coordinates of Maya main window."""
    maya_main_window = pc.language.getMelGlobal('string', 'gMainWindow')
    t, l = pc.window(maya_main_window, q=True, tlc=True)
    w, h = pc.window(maya_main_window, q=True, wh=True)
    center = l + w / 2
    mid = t + h / 2
    return (center, mid)


def center_window(win):
    """Places the given pymel window instance cetered over Maya main window."""
    center, mid = get_main_window_center()
    win_width, win_height = win.getWidthHeight()
    win.setTopLeftCorner((mid - win_height / 2, center - win_width / 2))


def get_selected_channelbox_attributes():
    """Returns the user-selected attributes in the maya main channelbox."""
    return pc.mel.eval("selectedChannelBoxAttributes();")
