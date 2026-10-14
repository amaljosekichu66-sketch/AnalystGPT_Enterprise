"""
Documentation guards from the Sprint 15 Readiness Gate.

- P3-03: documents referred to files that did not exist (MASTER_PROMPT.md,
  ENGINEERING_OPERATING_SYSTEM.md, 'ADR/', wrong-case names that only resolve
  on Windows). Every relative markdown link must resolve to a real file.
- P1-03: the gate documents disagreed on whether Sprint 15 could start. The
  start condition is written once and must read the same in each of them.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
LINK = re.compile(r'!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)')
FENCE = re.compile(r"^\s*(```|~~~)")


def _markdown_files() -> list[Path]:
    return [REPO / "README.md", REPO / "CHANGELOG.md", *sorted((REPO / "docs").rglob("*.md"))]


def _relative_links(path: Path):
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK.finditer(re.sub(r"`[^`]*`", "", line)):
            target = match.group(1)
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target = target.split("#", 1)[0].split("?", 1)[0]
            if target:
                yield number, target


def _exists_with_exact_case(path: Path) -> bool:
    """Path.exists() ignores case on Windows and macOS; CI runs on Linux, where it matters."""
    try:
        relative = path.resolve().relative_to(REPO)
    except ValueError:
        return path.exists()
    current = REPO
    for part in relative.parts:
        if part not in {child.name for child in current.iterdir()} if current.is_dir() else set():
            return False
        current = current / part
    return True


def test_every_relative_markdown_link_resolves() -> None:
    broken = [
        f"{path.relative_to(REPO).as_posix()}:{number} -> {target}"
        for path in _markdown_files()
        for number, target in _relative_links(path)
        if not _exists_with_exact_case(path.parent / target)
    ]
    assert not broken, "broken documentation links:\n" + "\n".join(broken)


START_CONDITION = (
    "Sprint 15 may start once every P1 item of the Sprint 15 Readiness Gate (2026-09-29 audit) is "
    "closed, which happens with the v14.1.0 release (the hardening merged to `main` through a green "
    "CI run and tagged `v14.1.0`), and a readiness re-audit of `v14.1.0` confirms it."
)


@pytest.mark.parametrize(
    "document",
    ["docs/engineering/PROJECT_STATE.md", "docs/project/ROADMAP.md", "docs/project/PROJECT_JOURNAL.md"],
)
def test_gate_documents_state_one_start_condition(document: str) -> None:
    text = " ".join((REPO / document).read_text(encoding="utf-8").split())
    assert START_CONDITION in text
    for stale in ("Sprint 15 may now start", "may begin now that v14.0.0 is released"):
        assert stale not in text
