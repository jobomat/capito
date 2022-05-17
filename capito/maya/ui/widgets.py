from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import re
import pymel.core as pc


def file_chooser(tfbGrp, fileMode, callback, **kwargs):
    target = pc.fileDialog2(
        dialogStyle=2, fileMode=fileMode, **kwargs
    )
    if not target:
        return
    if callback:
        if not callback(target[0]):
            tfbGrp.setText("")
            return
    tfbGrp.setText(target[0])


def file_chooser_button(label, fileMode, bl="...", text="",
                        tfb_kwargs=None, callback=None, **kwargs):
    """
    A label, textfield, button combo where:
        - the button will trigger a filedialog2 with kwargs
        - the text returned by filedialog will be set as text for the textfield
        - if callback (function) is set it will be handed the text
          and only if callback returns True the textfield will be set 
    fileMode    0 Any file, whether it exists or not.
                1 A single existing file.
                2 The name of a directory. Both directories and files are displayed in the dialog.
                3 The name of a directory. Only directories are displayed in the dialog.
                4 Then names of one or more existing files.
    callback    function to call after user has chosen file.
                The chosen file-string will be passed to this function.
    """
    tfb_kwargs = tfb_kwargs if tfb_kwargs is not None else {}
    btn = pc.textFieldButtonGrp(
        label=label, bl=bl, adj=2, text=text,
        cl3=["left", "center", "right"], ct3=["left", "both", "right"],
        **tfb_kwargs
    )
    btn.buttonCommand(
        pc.Callback(
            file_chooser, btn, fileMode=fileMode,
            callback=callback, **kwargs
        )
    )
    return btn
