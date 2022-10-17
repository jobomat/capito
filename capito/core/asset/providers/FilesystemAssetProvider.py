"""Module for a file based Asset Provider"""
import json
from pathlib import Path

from capito.conf.config import CONFIG
from capito.core.asset.models import Asset
from capito.core.asset.providers.baseclass import AssetProvider


class FilesystemAssetProvider(AssetProvider):
    """Asset Provider without any kind of database.
    This Provider relies purely on
    directories, files and json-files for metadata.
    This can be suboptimal for decentralized teamwork
    with cloud based filesharing because of the
    decentralized groundtruth.
    (Multiple and not really in syc versions on local drives...)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reload()

    def _read_asset_dir(self):
        abs_asset_path = Path(CONFIG.CAPITO_PROJECT_DIR) / CONFIG.ASSETS_PATH
        for asset_path in [d for d in abs_asset_path.iterdir() if d.is_dir()]:
            self._read_asset(asset_path)

    def _read_asset(self, path: Path):
        name = path.stem
        asset_meta = path / f"{name}.json"
        meta_dict = json.loads(asset_meta.read_text())
        asset = Asset(name, meta_dict["kind"])
        for step in meta_dict["steps"]:
            asset.add_step(step)
        for _, step in asset.steps.items():
            version_folder = Path(step.absolute_path) / "versions"
            for version in version_folder.glob("*.json"):
                step.add_version_from_json_file(version)
        self._add_asset(asset)

    def get(self, name: str):
        """Get a single asset by name."""
        return self.assets[name]

    def list(self):
        """Get the asset dictionary. {name: Asset}"""
        return self.assets

    def reload(self) -> None:
        """Reload the whole dictionary."""
        self.assets = {}
        self._read_asset_dir()
