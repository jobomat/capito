"""Module for a mock Asset Provider"""
from typing import Dict

from capito.core.asset.models import Asset
from capito.core.asset.providers.baseclass import AssetProvider


class MockAssetProvider(AssetProvider):
    """Mock"""

    def __init__(self) -> None:
        self.assets = {}
        self.assets["bob"] = Asset("bob", "char")
        self.assets["table"] = Asset("table", "prop")
        self.assets["chair"] = Asset("chair", "prop")
        self.assets["bowl"] = Asset("bowl", "prop")
        self.assets["spoon"] = Asset("spoon", "prop")
        self.assets["kitchen"] = Asset("kitchen", "set")
        self.assets["breakfast"] = Asset("breakfast", "sequ")
        self.assets["shot001"] = Asset("shot001", "shot")
        self.assets["shoe002"] = Asset("shot002", "shot")
        self.assets["test"] = Asset("test", "omni")

    def get(self, name: str) -> Asset:
        """Returns  Asset by name"""
        return self.assets[name]

    def list(self) -> Dict[str, Asset]:
        """Returns a dict of all Assets"""
        return self.assets
