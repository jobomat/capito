from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from capito.core.models import Asset


class AssetProvider(ABC):
    @abstractmethod
    def get_asset(self, name: str) -> Asset:
        """Returns  Asset by name"""

    @abstractmethod
    def get_assets(self) -> List[Asset]:
        """Returns a list of all Assets"""
