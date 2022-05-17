import os
import site
from capito.maya.environ.vars import getenv

site.addsitedir(
    os.path.normpath(
        os.path.join(getenv("CG3_MAYA_DIR"), "venvs", "cg3", "Lib", "site-packages")
    )
)
