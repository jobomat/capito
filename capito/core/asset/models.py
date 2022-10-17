import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import capito.core.event as capito_event
import pytz
from capito.conf.config import CONFIG
from capito.core.helpers import time_from_ntp
from capito.core.user.models import User

#  TODO: STEPS sollte aus einer externen Quelle kommen
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
    user: str
    extension: str
    _comment: str = None
    timestamp: float = None
    representations: Optional[Dict[str, Representation]] = field(default_factory=dict)

    def __post_init__(self):
        self.timestamp = self.timestamp or time_from_ntp()

    def save_json(self):
        """Save the unique json file on creation of a version."""
        content = {
            "version": self.version,
            "user": self.user,
            "extension": self.extension,
            "comment": self.comment,
            "timestamp": self.timestamp,
        }
        json_file = Path(self.absolute_path) / f"{self.file}.json"
        json_file.parent.mkdir(parents=True, exist_ok=True)
        with json_file.open("w") as jfp:
            json.dump(content, jfp)

    def get_date(self, pattern: str):
        """Human readable date with specifiable string pattern."""
        return datetime.fromtimestamp(
            self.timestamp, tz=pytz.timezone(CONFIG.TIMEZONE)
        ).strftime(pattern)

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
    def filepath(self):
        """Get absolute path and filename"""
        return f"{self.absolute_path}/{self.file}"

    @property
    def date(self):
        """Human readable date property"""
        return self.get_date("%d.%m.%y - %H:%M")

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment):
        self._comment = comment
        self.save_json()
        capito_event.post("version_changed", self)

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
    asset: "Asset" = None
    versions: Optional[Dict[str, Version]] = field(default_factory=dict)
    contains: Optional[List[Release]] = field(default_factory=list)
    status: str = "NONE"

    def add_version(
        self,
        version: int,
        user: str,
        extension: str,
        comment: str = None,
        timestamp: int = None,
    ):
        """Append a Version explicitly"""
        self.versions[version] = Version(
            version, self, user, extension, comment, timestamp
        )

    def add_version_from_json_file(self, json_file: Path):
        """Add a version from content of its json meta file."""
        with json_file.open("r", encoding="utf-8") as vjf:
            version_dict = json.load(vjf)
            version_dict["step"] = self
            self.add_version(**version_dict)

    def new_version(self, extension: str, comment: str = None, user: User = None):
        """Use next available version number."""
        user = user or os.environ.get("CAPITO_USERNAME")
        self.add_version(self.get_latest_version_number() + 1, user, extension, comment)
        capito_event.post("version_created", self.get_latest_version())

    def get_latest_version(self):
        """Get latest Version Instance of this Asset.step"""
        return self.versions[self.get_latest_version_number()]

    def get_latest_version_number(self):
        """Get latest version number."""
        return len(self.versions.keys())

    def create(self):
        """Create dirs, templates..."""
        abs_path = Path(self.absolute_path)
        version_path = CONFIG.VERSION_PATH.format(STEP_PATH=abs_path)
        representation_path = CONFIG.REPRESENTATION_PATH.format(
            VERSION_PATH=version_path
        )
        Path(version_path).mkdir(parents=True, exist_ok=True)
        Path(representation_path).mkdir(parents=True, exist_ok=True)

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
    flow: str = None


@dataclass
class Asset:
    """Class representing a unique Asset."""

    name: str
    kind: str
    steps: Dict[str, Step] = field(default_factory=dict)
    comment: str = None

    def add_step(self, step: str):
        """Append a Step."""
        self.steps[step] = Step(step, self)

    def step(self, step: str):
        """Get Step Instance (mod, rig, shade, shot...)"""
        return self.steps[step]

    def create(self):
        """Create a new asset.
        (Create directories, templates...)"""
        abs_asset_path = Path(CONFIG.CAPITO_PROJECT_DIR) / CONFIG.ASSETS_PATH
        asset_dir = abs_asset_path / self.name
        asset_dir.mkdir(parents=True, exist_ok=True)
        step_list = []
        for step in self.steps.values():
            step.create()
            step_list.append(f'"{step}"')
        meta_json = asset_dir / f"{self.name}.json"
        meta_json.touch()
        meta_json.write_text(
            f'{{"kind": "{self.kind}", "steps": [{",".join(step_list)}]}}'
        )
        capito_event.post("asset_created")

    def __str__(self):
        return self.name
