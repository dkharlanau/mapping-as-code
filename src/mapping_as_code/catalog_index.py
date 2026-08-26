from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .core import mapping_summary
from .governance import canonical_hash
from .io import load_document

_ALLOWED_SUFFIXES = {".yaml", ".yml", ".json"}
_DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".mapping-as-code",
    "conformance",
    "schema",
}


def _candidate_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in _ALLOWED_SUFFIXES else []
    if not root.is_dir():
        raise ValueError(f"catalog root does not exist: {root}")
    result: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _ALLOWED_SUFFIXES:
            continue
        relative_parts = path.relative_to(root).parts[:-1]
        if any(part in _DEFAULT_EXCLUDED_DIRS for part in relative_parts):
            continue
        result.append(path)
    return sorted(result, key=lambda item: item.as_posix())


def _strings(values: list[Any]) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value or "").strip()})


def _catalog_entry(document: dict[str, Any], *, path: str) -> dict[str, Any] | None:
    mapping = document.get("mapping")
    if not isinstance(mapping, dict):
        return None
    mapping_id = str(mapping.get("id") or "").strip()
    if not mapping_id:
        return None
    source = mapping.get("source") if isinstance(mapping.get("source"), dict) else {}
    target = mapping.get("target") if isinstance(mapping.get("target"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    owners: list[Any] = []
    criticalities: list[Any] = []
    for item in fields:
        if not isinstance(item, dict):
            continue
        business = item.get("business") if isinstance(item.get("business"), dict) else {}
        owners.append(business.get("owner"))
        criticalities.append(business.get("criticality"))
    summary = mapping_summary(document)
    return {
        "path": path,
        "mapping_id": mapping_id,
        "title": mapping.get("title"),
        "description": mapping.get("description"),
        "source": {"system": source.get("system"), "object": source.get("object")},
        "target": {"system": target.get("system"), "object": target.get("object")},
        "field_mappings": summary["field_mappings"],
        "required_target_coverage": summary["coverage"],
        "owners": _strings(owners),
        "criticalities": _strings(criticalities),
        "canonical_sha256": canonical_hash(document),
    }


def build_catalog_index(root: str | Path) -> dict[str, Any]:
    root_path = Path(root).resolve()
    entries: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for path in _candidate_files(root_path):
        display_path = path.name if root_path.is_file() else path.relative_to(root_path).as_posix()
        try:
            document = load_document(path)
        except (OSError, ValueError, TypeError) as exc:
            skipped.append({"path": display_path, "reason": str(exc)})
            continue
        if not isinstance(document, dict):
            continue
        entry = _catalog_entry(document, path=display_path)
        if entry is not None:
            entries.append(entry)

    by_id: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        by_id[entry["mapping_id"]].append(entry["path"])
    duplicates = [
        {"mapping_id": mapping_id, "paths": sorted(paths)}
        for mapping_id, paths in sorted(by_id.items())
        if len(paths) > 1
    ]
    return {
        "catalog_version": 1,
        "root": root_path.name if root_path.is_dir() else root_path.parent.name,
        "mappings": sorted(entries, key=lambda item: (item["mapping_id"], item["path"])),
        "duplicates": duplicates,
        "skipped": skipped,
        "summary": {
            "mapping_documents": len(entries),
            "duplicate_mapping_ids": len(duplicates),
            "skipped_documents": len(skipped),
        },
    }


def _search_text(entry: dict[str, Any]) -> str:
    values = [
        entry.get("path"),
        entry.get("mapping_id"),
        entry.get("title"),
        entry.get("description"),
        entry.get("source", {}).get("system"),
        entry.get("source", {}).get("object"),
        entry.get("target", {}).get("system"),
        entry.get("target", {}).get("object"),
        *entry.get("owners", []),
        *entry.get("criticalities", []),
    ]
    return " ".join(str(value) for value in values if value is not None).casefold()


def search_catalog(index: dict[str, Any], query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    phrase = str(query or "").strip().casefold()
    if not phrase:
        raise ValueError("query must not be empty")
    tokens = [token for token in phrase.split() if token]
    matches: list[tuple[int, dict[str, Any]]] = []
    for entry in index.get("mappings", []):
        if not isinstance(entry, dict):
            continue
        text = _search_text(entry)
        if not all(token in text for token in tokens):
            continue
        score = 10 * sum(text.count(token) for token in tokens)
        mapping_id = str(entry.get("mapping_id") or "").casefold()
        title = str(entry.get("title") or "").casefold()
        path = str(entry.get("path") or "").casefold()
        if mapping_id == phrase:
            score += 100
        if phrase in title:
            score += 30
        if phrase in path:
            score += 15
        matches.append((score, entry))
    matches.sort(key=lambda item: (-item[0], str(item[1].get("mapping_id")), str(item[1].get("path"))))
    return [{"score": score, **entry} for score, entry in matches[:limit]]
