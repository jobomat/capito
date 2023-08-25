import inspect
from pathlib import Path
import sys


this_file_path = inspect.getfile(lambda: None)
print(this_file_path)