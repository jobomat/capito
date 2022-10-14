from typing import Dict, List, Tuple

import capito.core.event as capito_event

# from oauth2client.service_account import ServiceAccountCredentials
import gspread
from capito.conf.config import CONFIG
from capito.core.asset.flows import FlowProvider
from capito.core.asset.models import Asset
from capito.core.asset.providers.baseclass import AssetProvider
from capito.core.asset.providers.exceptions import AssetExistsError


class GoogleSheetsAssetProvider(AssetProvider):
    """Google Sheets API Connector"""

    def __init__(self):
        if not CONFIG.google_connector:
            CONFIG.google_connector = gspread.service_account(
                filename=CONFIG.GOOGLE_API_KEY_JSON
            )
        self.asset_sheet = CONFIG.google_connector.open(
            CONFIG.GOOGLE_SHEETS_NAME
        ).sheet1
        self.assets = {}
        self.reload()

    def _sort_asset_sheet(self):
        # sort by asset, step, version
        # so the reload_asset_list method will work correct
        self.asset_sheet.sort((1, "asc"), (3, "asc"), (4, "asc"))

    def reload(self):
        """Reload"""
        self.assets = {}
        self._sort_asset_sheet()
        results = self.asset_sheet.get_all_records()

        current_asset_name = None
        current_step = None

        for result in results:
            asset_name = result["asset"]

            if current_asset_name != asset_name:
                current_asset_name = result["asset"]
                self.assets[current_asset_name] = Asset(
                    current_asset_name, result["kind"]
                )
                current_step = None
                continue

            if current_step != result["step"]:
                current_step = result["step"]
                self.assets[current_asset_name].add_step(current_step)
                self.assets[current_asset_name].steps[current_step].status = result[
                    "status"
                ]
                continue
            self.assets[current_asset_name].steps[current_step].add_version(
                result["version"],
                result["user"],
                result["extension"],
                result["comment"],
                timestamp=result["timestamp"],
            )

    def get(self, name: str) -> Asset:
        return self.assets.get(name, None)

    def list(self) -> Dict[str, Asset]:
        return self.assets

    def create_asset(self, name: str, kind: str):
        """Add all necessary rows."""
        try:
            asset = super().create_asset(name, kind)
        except AssetExistsError:
            print("Asset already exists")
            return

        # create the first asset line (without steps etc.)
        self.asset_sheet.append_row(
            (asset.name, asset.kind, 0, 0, None, None, None, None, None, None)
        )
        # create the first step rows (with version number 0)
        for step in asset.steps:
            self.asset_sheet.append_row(
                (asset.name, None, step, 0, None, "NONE", None, None, None)
            )

        self.reload()

    def create_assets(self, asset_tuples: List[Tuple[str, str]]):
        """Add multiple rows to reduce API calls."""
        assets = super().create_assets(asset_tuples)
        rows = []
        for asset in assets:
            if not asset:
                continue
            rows.append(
                [asset.name, asset.kind, 0, 0, None, None, None, None, None, None]
            )
            for step in asset.steps:
                rows.append(
                    (asset.name, None, step, 0, None, step.status, None, None, None)
                )
            capito_event.post("asset_created")
        self.asset_sheet.append_rows(rows)
