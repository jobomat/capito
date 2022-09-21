from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict

from capito.core.asset.models import Asset


class AssetProvider(ABC):
    """The base class for Asset Providers."""

    @abstractmethod
    def get(self, name: str) -> Asset:
        """Returns  Asset by name"""

    @abstractmethod
    def list(self) -> Dict[str, Asset]:
        """Returns a dictionary of all Assets"""
