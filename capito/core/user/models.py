from dataclasses import dataclass, field
from typing import List


@dataclass
class User:
    name: str
    long_name: str = None
    email: str = None

    def __str__(self):
        return self.name
