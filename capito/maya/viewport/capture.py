import os.path
import pymel.core as pc
from cg.maya.utils.images import get_size


def cleanup(cam, delete_cam_on_close, other_win_name):
    if pc.window(other_win_name, exists=True):
        pc.window(other_win_name, e=True, closeCommand=lambda: "")
        pc.deleteUI(other_win_name)
    if delete_cam_on_close:
        pc.delete(cam)


def adjust_viewport_size(intField, win):
    win.setWidth(intField.getValue1())
    win.setHeight(intField.getValue2())


def screenshot(cam=None, viewportsize=[640, 360], imagesize=None, callback=None,
               save_path=None, filename=None, enable_ui=True,
               formats=["png", "bmp", "jpg"], close_after_capture=True):
    imagesize = imagesize or viewportsize

    delete_cam_on_close = False
    if cam is None:
        try:
            cam = pc.PyNode("temporary_screenshot_cam")
        except pc.MayaNodeError:
            cam = pc.camera(
                position=(2, 2.5, 2), rotation=(-40, 45, 0),
                name="temporary_screenshot_cam"
            )[0]
        delete_cam_on_close = True

    viewport_win_name = 'capture_viewport_win'
    control_win_name = 'capture_control_win'

    if pc.window(viewport_win_name, exists=True):
        pc.deleteUI(viewport_win_name)
    if pc.window(control_win_name, exists=True):
        pc.deleteUI(control_win_name)

    viewport_win = pc.window(
        viewport_win_name, w=viewportsize[0], h=(viewportsize[1]),
        maximizeButton=False, minimizeButton=False, title="Capture Viewport",
        sizeable=False
    )

    with viewport_win:
        with pc.formLayout(numberOfDivisions=100) as main_layout:
            modeleditor = pc.modelEditor(av=True)

    pc.modelEditor(
        modeleditor, e=1, camera=cam, headsUpDisplay=False, grid=False, cameras=False,
        displayAppearance="smoothShaded"
    )

    main_layout.attachForm(modeleditor, 'top', 0)
    main_layout.attachForm(modeleditor, 'left', 0)
    main_layout.attachForm(modeleditor, 'right', 0)
    main_layout.attachForm(modeleditor, 'bottom', 0)


    with pc.window(control_win_name, title="Capture Control", w=320) as control_win:
        with pc.columnLayout(adj=True):
            viewport_wh_intfield = pc.intFieldGrp(
                numberOfFields=2, label="Viewport w | h",
                v1=viewportsize[0], v2=viewportsize[1],
                enable=enable_ui, cw3=(80,80,80), adj=3
            )
            path_textfield = pc.textFieldGrp(
                label="Save Path",
                text=save_path, enable=enable_ui, cw2=(80,160), adj=2
            )

            filename_textfield = pc.textFieldGrp(
                label="Filename",
                text=filename, enable=enable_ui, cw2=(80,160), adj=2
            )

            with pc.rowLayout(nc=2, cw2=(80,160), cl1="right", adj=2):
                pc.text(label="Fileformat", align="right")
                with pc.optionMenu(enable=enable_ui) as format_optionmenu:
                    for fileformat in formats:
                        pc.menuItem(label=fileformat)

            capture_button = pc.button(label='Capture', bgc=(.9,0,0))

    viewport_wh_intfield.changeCommand(
        pc.Callback(adjust_viewport_size, viewport_wh_intfield, viewport_win)
    )
    capture_button.setCommand(pc.Callback(
        capture, cam,
        {"modeleditor": modeleditor, "path_textfield": path_textfield,
         "filename_textfield": filename_textfield, "viewport_win": viewport_win,
         "format_optionmenu": format_optionmenu, "control_win": control_win},
        callback, close_after_capture
    ))

    control_win.closeCommand(pc.Callback(cleanup, cam, delete_cam_on_close, viewport_win_name))
    viewport_win.closeCommand(pc.Callback(cleanup, cam, delete_cam_on_close, control_win_name))

    viewport_win.setWidthHeight(viewportsize)


def capture(cam, ui, callback, close_after_capture):
    path = ui["path_textfield"].getText()
    filename = ui["filename_textfield"].getText()
    fileformat = ui["format_optionmenu"].getValue()
    f = os.path.join(path, filename + '.' + fileformat)
    ui["modeleditor"].setCapture(f)
    cam.setTranslation(cam.getTranslation())
    pc.refresh()
    w, h = get_size(f)

    if close_after_capture:
        pc.deleteUI(ui["control_win"])

    if callback is not None:
        callback(f, w, h)


# def api_capture(cam, ui, path, filename, fileformat, callback):
#     f = os.path.join(path, filename + '.' + fileformat)
#     pc.refresh()
#     image = api.MImage()
#     #   Bug Workaraound:
#     #   "Move" Cam or otherwise the imagebuffer will be black
#     #   if the cam wasn't used by the user... ???
#     cam.setTranslation(cam.getTranslation())

#     view = apiUI.M3dView.active3dView()
#     view.refresh()
#     view.readColorBuffer(image, True)
#     w = ui["resample_intfield"].getValue1()
#     h = ui["resample_intfield"].getValue2()
#     image.resize(w, h, True)
#     #   Write image into a file:
#     image.writeToFile(f, fileformat)
#     # pc.modelEditor(modeleditor, edit=1, capture=f)
#     if callback is not None:
#         callback(f)
