import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from capito.conf.config import CONFIG
from capito.core.asset.flows import Flows
from capito.core.helpers import time_from_ntp
from capito.core.user.models import User

STEPS = {
    "mod": "Modelling",
    "rig": "Rigging",
    "shade": "Shading",
    "groom": "Grooming",
    "anim": "Animation",
    "light": "Lighting",
    "asmbl": "Assembly",
    "ren": "Rendering",
    "comp": "Compositing",
    "edit": "Editing",
    "grade": "Grading",
    "fx": "Effects",
}


@dataclass
class Representation:
    """Class representing Files of Asset.Step.Version.
    Representations exclude the version-workfile itself, as it
    is already represented by the Version classes path and file methods.
    Representations are e.g. a turntable rendering as mp4 or
    a thumbnail as jpg or other files representing this version.
    """

    version: "Version"
    extension: str
    description: str = ""

    def __post_init__(self):
        if not self.description:
            self.description = str(len(self.version.representations[self.extension]))

    @property
    def step(self):
        """Convenience shortcut to get the step."""
        return self.version.step

    @property
    def asset(self):
        """Convenience shortcut to get the asset."""
        return self.version.asset


@dataclass
class Version:
    """Class representing a Version of a Step of an Asset."""

    version: int
    step: "Step"
    user: User
    extension: str
    comment: str = None
    timestamp: float = None
    representations: Optional[Dict[str, Representation]] = field(default_factory=dict)

    def __post_init__(self):
        self.timestamp = self.timestamp or time_from_ntp()

    @property
    def absolute_path(self):
        """Returns the absolute path of version workfile on the current computer."""
        return CONFIG.VERSION_PATH.format(STEP_PATH=self.step.absolute_path)

    @property
    def relative_path(self):
        """Returns the path without the base-path and asset folder."""
        return CONFIG.VERSION_PATH.format(STEP_PATH=self.step.relative_path)

    @property
    def file(self):
        """Get filename only"""
        return CONFIG.VERSION_FILE.format(
            asset=self.asset,
            step=self.step,
            version=str(self),
            user=self.user,
            time=self.timestamp,
            extension=self.extension,
        )

    @property
    def asset(self) -> "Asset":
        """Return corresponding Asset."""
        return self.step.asset

    def __str__(self) -> str:
        return str(self.version).zfill(4)


@dataclass
class Release:
    """Class of a published 'fixed' Release"""

    name: str
    based_on: Version
    contained_in: Optional[List["Step"]] = field(default_factory=list)


@dataclass
class Step:
    """Class representing a working step (~Department mod, rig...)."""

    name: str
    long_name: str
    asset: "Asset" = None
    versions: Optional[Dict[str, Version]] = field(default_factory=dict)
    contains: Optional[List[Release]] = field(default_factory=list)

    def add_version(
        self,
        version: int,
        user: User,
        extension: str,
        comment: str = None,
        timestamp: int = None,
    ):
        """Append a Version explicitly"""
        self.versions[version] = Version(
            version, self, user, extension, comment, timestamp
        )

    def new_version(self, extension: str, comment: str = None, user: User = None):
        """Use next available version number."""
        user = user or os.environ.get("CAPITO_USERNAME")
        self.add_version(self.get_latest_version_number() + 1, user, extension, comment)

    def get_latest_version(self):
        """Get latest Version Instance of this Asset.step"""
        return self.versions[self.get_latest_version_number()]

    def get_latest_version_number(self):
        """Get latest version number."""
        return len(self.versions.keys())

    @property
    def relative_path(self):
        """Returns the relative path of step dir."""
        return CONFIG.STEP_PATH.format(
            ASSETS_PATH=CONFIG.ASSETS_PATH, asset=self.asset, step=self.name
        )

    @property
    def absolute_path(self):
        """Returns the absolute path of step dir on current computer."""
        project_path = os.environ.get("CAPITO_PROJECT_DIR")
        if project_path is not None:
            return f"{project_path}/{self.relative_path}"

    def __str__(self):
        return self.name


@dataclass
class Kind:
    """Class representing a kind of asset. (character, prop, set, shot...)"""

    name: str
    long_name: str
    flow: Flows = None


@dataclass
class Asset:
    """Class representing a unique Asset."""

    name: str
    kind: str
    steps: Dict[str, Step] = field(default_factory=dict)

    def add_step(self, step: str):
        """Append a Step and annotate it."""
        self.steps[step] = Step(step, STEPS[step], self)

    def step(self, step: str):
        """Get Step Instance (mod, rig, shade, shot...)"""
        return self.steps[step]

    def __str__(self):
        return self.name


# from pathlib import Path
# from capito.core.asset.models import Asset


# bob = Asset("bob", "char")
# bob.add_step("mod")
# bob.add_step("rig")
# bob.add_step("shade")

# for step in bob.steps.values():
#     Path(step.absolute_path).mkdir(parents=True, exist_ok=True)
