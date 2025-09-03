from dataclasses import dataclass

@dataclass
class Policy:
    max_fpr: float = 0.005   # 0.5% threshold
    require_justification: bool = True
    allowed_targets: tuple[str,...] = ("splunk","elastic","sql")
    require_adapter: bool = True

DEFAULT_POLICY = Policy()