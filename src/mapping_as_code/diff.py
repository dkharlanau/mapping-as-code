from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MappingDiff:
    added: list[dict[str, Any]]
    removed: list[dict[str, Any]]
    changed: list[dict[str, Any]]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def as_dict(self) -> dict[str, Any]:
        return {"added": self.added, "removed": self.removed, "changed": self.changed}


def diff_documents(before: dict[str, Any], after: dict[str, Any]) -> MappingDiff:
    old = {field["id"]: field for field in before.get("fields", [])}
    new = {field["id"]: field for field in after.get("fields", [])}
    added = [{"id": key, "after": new[key]} for key in sorted(new.keys() - old.keys())]
    removed = [{"id": key, "before": old[key]} for key in sorted(old.keys() - new.keys())]
    changed = [{"id": key, "before": old[key], "after": new[key]} for key in sorted(old.keys() & new.keys()) if old[key] != new[key]]
    return MappingDiff(added=added, removed=removed, changed=changed)
