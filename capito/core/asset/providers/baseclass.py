"""Baseclass module for all AssetProviders."""
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Tuple

import capito.core.event as capito_event
from capito.core.asset.flows import FlowProvider
from capito.core.asset.models import Asset
from capito.core.asset.providers.exceptions import AssetExistsError


class AssetProvider(object, metaclass=ABCMeta):
    """The base class for Asset Providers."""

    @abstractmethod
    def __init__(self, flow_provider: FlowProvider):
        self.flow_provider = flow_provider
        self.assets = {}

    @abstractmethod
    def get(self, name: str) -> Asset:
        """Returns  Asset by name"""

    @abstractmethod
    def list(self) -> Dict[str, Asset]:
        """Returns a dictionary of all Assets"""

    @abstractmethod
    def reload(self) -> None:
        """Reloads the asset list."""

    def asset_exists(self, name:str) -> bool:
        if not self.assets.get(name):
            return True
        return False

    def add_asset(self, asset: Asset):
        """Convenience for adding to the asset dict."""
        self.assets[asset.name] = asset

    def create_asset(self, name: str, kind: str) -> Asset:
        """Create a new asset and add it to providers list."""
        if name in self.assets:
            raise AssetExistsError(f"Asset of name '{name}' already exists.")
        if self.flow_provider is None:
            print("No FlowProvider abailible in AssetProvider.")
            return
        flow = self.flow_provider.flows.get(kind)
        if flow is None:
            print(
                f"Flow for '{flow}' not availible in FlowProvider (in AssetProvider)."
            )
            return
        asset = Asset(name, kind)
        for step in flow.steps:
            asset.add_step(step)
        asset.create()
        self.add_asset(asset)
        capito_event.post("asset_created")
        return asset

    def create_assets(self, asset_tuples: List[Tuple[str, str]]) -> List[Tuple[str, Asset]]:
        """For bulk creation. Overwrite this, if it's better to
        treat bulk creation differently. Otherwise it will just
        default to multiple calls of self.create_asset.
        
        PLEASE MIND:
        If this method is overridden and doesn't call self.create_asset:
        For each created Asset you HAVE TO POST THE EVENT:
        capito_event.post("asset_created")
        """
        assets = []
        for name, kind in asset_tuples:
            try:
                asset = self.create_asset(name, kind)
            except AssetExistsError:
                continue
            assets.append(asset)
        return assets
