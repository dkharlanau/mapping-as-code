from __future__ import annotations

import json
import re
from pathlib import Path

from mapping_as_code.cli import build_parser


ROOT = Path(__file__).parents[1]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def test_local_markdown_links_resolve():
    documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    broken: list[str] = []
    for document in documents:
        for raw_target in LINK_RE.findall(document.read_text(encoding="utf-8")):
            target = raw_target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (document.parent / target).resolve().exists():
                broken.append(f"{document.relative_to(ROOT)} -> {raw_target}")
    assert not broken, "Broken local documentation links:\n" + "\n".join(broken)


def test_agent_manifest_uses_supported_cli_commands():
    manifest = json.loads((ROOT / "docs" / "agent-manifest.json").read_text(encoding="utf-8"))
    parser = build_parser()
    command_action = next(action for action in parser._actions if action.dest == "command")
    supported = set(command_action.choices)
    advertised = {entry["command"].split()[1] for entry in manifest["entrypoints"] if entry["type"] == "cli"}
    assert advertised <= supported


def test_public_guidance_does_not_advertise_retired_interface():
    guidance = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in ("AGENTS.md", "docs/agent-manifest.json", "docs/product.html")
    )
    assert "python -m mac" not in guidance
    for command in ("mac schema", "mac coverage", "mac compile", "mac evidence-bundle"):
        assert command not in guidance
