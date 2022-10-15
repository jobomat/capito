from typing import Any, Dict, List, Tuple, Union

import capito.core.event as capito_event
import gspread
from capito.conf.config import CONFIG
from capito.core.asset.flows import FlowProvider
from capito.core.asset.models import Asset, Step, Version
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
        self.keys = {
            "asset": "A",
            "kind": "B",
            "step": "C",
            "version": "D",
            "comment": "E",
            "status": "F",
            "user": "G",
            "timestamp": "H",
            "publish": "I",
            "extension": "J",
            "uid": "K",
        }
        self.assets = {}
        capito_event.subscribe("version_created", self._add_version_row)
        self.reload()

    def _add_version_row(self, version: Version):
        self.asset_sheet.append_row(
            (
                version.asset.name,
                None,
                version.step.name,
                version.version,
                version.comment,
                None,
                version.user,
                version.timestamp,
                None,
                version.extension,
                f"uid_{version.asset.name}_{version.step.name}_{version.version}",
            )
        )
        self.asset_sheet.update(
            self._cell(self._infer_uid(version.step), "status"), "WIP"
        )
        self._sort_asset_sheet()

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
        """Get a single asset by name."""
        return self.assets.get(name, None)

    def list(self) -> Dict[str, Asset]:
        """Returns a dict of all Assets"""
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
            (
                asset.name,
                asset.kind,
                0,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                f"uid_{asset.name}_0_0",
            )
        )
        # create the first step rows (with version number 0)
        for step in asset.steps:
            self.asset_sheet.append_row(
                (
                    asset.name,
                    None,
                    step,
                    0,
                    None,
                    "NONE",
                    None,
                    None,
                    None,
                    None,
                    f"uid_{asset.name}_{step}_0",
                )
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
                (
                    asset.name,
                    asset.kind,
                    0,
                    0,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    f"uid_{asset.name}_0_0",
                )
            )
            for step in asset.steps:
                rows.append(
                    (
                        asset.name,
                        None,
                        step,
                        0,
                        None,
                        step.status,
                        None,
                        None,
                        None,
                        None,
                        f"uid_{asset.name}_{step}_0",
                    )
                )
        self.asset_sheet.append_rows(rows)

    def setattr(self, obj: Union[Asset, Step, Version], attr: str, value: Any):
        """Update the given attribute with the given value
        in asset, asset.step or asset.step.version"""
        super().setattr(obj, attr, value)
        self.asset_sheet.update(self._cell(self._infer_uid(obj), attr), value)

    def _infer_uid(self, obj: Union[Asset, Step, Version]):
        asset = None
        step = "0"
        version = 0
        if isinstance(obj, Asset):
            asset = obj.name
        elif isinstance(obj, Step):
            asset = obj.asset.name
            step = str(obj)
        elif isinstance(obj, Version):
            asset = obj.asset.name
            step = obj.step.name
            version = obj.version
        return f"uid_{asset}_{step}_{version}"

    def _cell(self, uid, key):
        uid_cell = self.asset_sheet.find(uid)
        return f"{self.keys[key]}{uid_cell.row}"
