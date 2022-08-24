from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from capito.core.helpers import time_from_ntp
from capito.core.user.models import User


@dataclass
class Representation:
    """Wrapper around the concrete File of Asset.Subset.Version"""

    relative_path: str
    extension: str  # ma, png, mp4 ...
    host: str
    user: User
    timestamp: int

    def path(self, base_path: Path):
        """Get the absolute Path to the Representation."""
        return Path(base_path + self.relative_path)


@dataclass
class Version:
    """Class representing a Version of a Subset of an Asset."""

    version: int
    timestamp: float
    representations: Optional[List[Representation]] = field(default_factory=list)
    parent: "Subset" = None

    def get_asset(self) -> "Asset":
        """Return corresponding Asset."""
        return self.parent.parent


@dataclass
class Release:
    """Class of a published 'fixed' Release"""

    based_on: Version
    contained_in: Optional[List["Subset"]] = field(default_factory=list)


@dataclass
class Subset:
    """Class representing a Subset which is a Child of an Asset."""

    family: str
    versions: Optional[List[Version]] = field(default_factory=list)
    contains: Optional[List[Release]] = field(default_factory=list)
    parent: "Asset" = None

    def add_version(self, version: Version):
        """Append a Version"""
        self.versions.append(version)
        version.parent = self

    def version(self, version: int) -> Version:
        """Get specific Version of this Subset."""
        versions = [v for v in self.versions if v.version == version]
        if versions:
            return versions[0]
        new_version = Version(1, time_from_ntp())
        self.add_version(new_version)
        return new_version

    def get_asset(self) -> "Asset":
        """Get corresponding Asset"""
        return self.parent


@dataclass
class Asset:
    """Class representing a unique Asset."""

    name: str
    subsets: Optional[List["Subset"]] = field(default_factory=list)

    def add_subset(self, subset: Subset):
        """Append a Subset and annotate it."""
        self.subsets.append(subset)
        subset.parent = self

    def subset(self, subset: str) -> Subset:
        """Get subset tagged 'subset'."""
        subsets = [s for s in self.subsets if s.family == subset]
        if subsets:
            return subsets[0]
        new_subset = Subset(subset)
        self.add_subset(new_subset)
        return new_subset


bob = Asset("bob")
bob_mod = Subset("mod")
bob.add_subset(bob_mod)
bob_mod_version1 = Version(1, time_from_ntp())
bob_mod.add_version(bob_mod_version1)

print(bob.subset("mod").version(1))
print(bob.subset("rig"))
