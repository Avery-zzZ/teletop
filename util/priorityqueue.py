from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class PQItem:
    priority: int
    item: Any=field(compare=False)