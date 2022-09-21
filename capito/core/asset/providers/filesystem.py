"""Module for a file based Asset Provider"""
from baseclass import AssetProvider


class FilesystemAssetProvider(AssetProvider):
    """Asset Provider without any kind of database.
    This Provider relies purely on
    directories, files and json-files for metadata.
    This can be suboptimal for decentralized teamwork
    with cloud based filesharing because of the
    decentralized groundtruth.
    (Multiple and not really in syc versions on local drives...)
    """

    def get(self, name):
        pass

    def list(self):
        pass
