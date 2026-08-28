from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OutboxDispatchResult:
    selected: int
    sent: int
    failed: int
