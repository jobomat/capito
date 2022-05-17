import contextlib

import pymel.core as pc


@contextlib.contextmanager
def maintained_selection():
    """Maintain selection during context
    """

    previous_selection = pc.selected()
    try:
        yield
    finally:
        if previous_selection:
            pc.select(previous_selection, replace=True, noExpand=True)
        else:
            pc.select(clear=True)
