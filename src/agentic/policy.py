from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Policy:
    max_fpr: float = 0.005   # 0.5% default
    require_adapter: bool = True
    allowed_targets: tuple[str,...] = ("splunk","elastic","sql")

DEFAULT_POLICY = Policy()