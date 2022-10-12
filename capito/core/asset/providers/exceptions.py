"""Module providing Exceptions for Asset specific operations."""


class AssetExistsError(Exception):
    """Raised when Asset with an already existing name should be created."""
    pass