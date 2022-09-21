"""Module for a mock Asset Provider"""
from typing import Dict

from capito.core.asset.models import Asset
from capito.core.asset.providers.baseclass import AssetProvider


class MockAssetProvider(AssetProvider):
    """Mock"""

    def __init__(self) -> None:
        self.assets = {}
        self.assets["bob"] = Asset("bob", "char")
        self.assets["book"] = Asset("book", "prop")
        self.assets["chair"] = Asset("chair", "prop")
        self.assets["chair2"] = Asset("chair2", "prop")
        self.assets["kitchen"] = Asset("kitchen", "set")
        self.assets["livingroom"] = Asset("livingroom", "set")
        self.assets["liz"] = Asset("liz", "char")
        self.assets["pete"] = Asset("pete", "char")
        self.assets["table"] = Asset("table", "prop")
        self.assets["table2"] = Asset("table2", "prop")
        self.assets["vase"] = Asset("vase", "prop")
        self.assets["vase2"] = Asset("vase2", "prop")

    def get(self, name: str) -> Asset:
        """Returns  Asset by name"""
        return self.assets[name]

    def list(self) -> Dict[str, Asset]:
        """Returns a dict of all Assets"""
        return self.assets
