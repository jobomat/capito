from typing import Any, List
from capito.core.pipe import Pipeable, PipeableCategory


class ExportAlembic(Pipeable):
    """Exports all items as Alembic cache file (abc)."""

    label = "Export Alembic"
    category = PipeableCategory.EXPORT
    host = "maya"

    def set_parameters(self, regex_pattern: str = None):
        """Set the parameters needed in 'execute'."""
        self.regex_pattern = regex_pattern

    def get_default_parameters(self):
        """A regular expression to match the items names against (eg '_(geo$|grp$)')."""
        return {"regex_pattern": "_(geo$|grp$)"}

    def execute(self, items: List[Any], exports: List[str]):
        """Export to Alembic."""
        
        long_names = [item.name(long=True) for item in items]
        objects = f"-root {' -root '.join(long_names)}"
        self.messages.append(f"{len(items)} objects exported as '{objects}'")
        # cmd = f'AbcExport -j "-frameRange {startframe} {endframe} -uvWrite -writeColorSets -writeFaceSets -worldSpace -autoSubd -writeUVSets -dataFormat ogawa {objects} -file {filename}";'
