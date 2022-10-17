import capito.core.event as capito_event
from capito.conf.config import CONFIG, reload
from capito.core.asset.flows import FlowProvider
from capito.core.asset.providers import (
    FilesystemAssetProvider,
    GoogleSheetsAssetProvider,
    MockAssetProvider,
)

PROVIDERS = {
    "Filesystem Based": FilesystemAssetProvider.FilesystemAssetProvider,
    "Google Sheets Based": GoogleSheetsAssetProvider.GoogleSheetsAssetProvider,
    "Mock": MockAssetProvider.MockAssetProvider,
}


def change_asset_provider():
    if CONFIG.ASSET_PROVIDER_TYPE:
        if not CONFIG.flow_provider:
            CONFIG.flow_provider = FlowProvider()
        CONFIG.asset_provider = PROVIDERS[CONFIG.ASSET_PROVIDER_TYPE]()
        capito_event.post("asset_list_changed")

capito_event.unsubscribe_by_name("asset_provider_changed", "change_asset_provider")
capito_event.subscribe("asset_provider_changed", change_asset_provider)

change_asset_provider()
