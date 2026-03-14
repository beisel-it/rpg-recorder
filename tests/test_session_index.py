"""
test_session_index.py — Tests for session index page generator (RPGREC-009).

All checks are pure string assertions on rendered HTML — no browser required.

Acceptance criteria:
  - index.html is written to sessions_dir
  - Each session card appears with id, date, duration, speakers, link
  - Lunr.js search docs JSON is embedded in the page
  - lunr.min.js is referenced as a local asset (no CDN)
  - Sessions are sorted newest-first
  - Empty sessions_dir → index.html still renders with zero cards
  - Sessions without transcript or metadata are handled gracefully
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bot.session_index import build_index


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session(
    sessions_dir: Path,
    name: str,
    *,
    date: str = "",
    duration_seconds: float = 0.0,
    speakers: list[str] | None = None,
    transcript: list[dict] | None = None,
    complete: bool = True,
) -> Path:
    """Create a minimal session sub-directory."""
    d = sessions_dir / name
    d.mkdir(parents=True, exist_ok=True)

    if complete:
        # write a stub index.html so the session is recognised as complete
        (d / "index.html").write_text("<html></html>", encoding="utf-8")

    if date or duration_seconds:
        meta = {}
        if date:
            meta["date"] = date
        if duration_seconds:
            meta["duration_seconds"] = duration_seconds
        (d / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")

    if transcript is not None:
        (d / "transcript.json").write_text(
            json.dumps(transcript, ensure_ascii=False), encoding="utf-8"
        )
    elif speakers:
        # Auto-generate a minimal transcript from the speaker list
        segs = [
            {"speaker": spk, "start": float(i * 10), "end": float(i * 10 + 5), "text": f"Hello from {spk}"}
            for i, spk in enumerate(speakers)
        ]
        (d / "transcript.json").write_text(json.dumps(segs), encoding="utf-8")

    return d


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sessions_dir(tmp_path: Path) -> Path:
    d = tmp_path / "sessions"
    d.mkdir()
    return d


@pytest.fixture
def populated(sessions_dir: Path) -> tuple[Path, str]:
    """Two complete sessions + one incomplete; returns (sessions_dir, html)."""
    _make_session(
        sessions_dir, "session-20260101-001",
        date="2026-01-01", duration_seconds=3723.0,
        speakers=["Alice", "Bob"],
    )
    _make_session(
        sessions_dir, "session-20260314-001",
        date="2026-03-14", duration_seconds=5400.0,
        speakers=["Alice", "GM"],
    )
    # Incomplete — no index.html; should be excluded
    _make_session(sessions_dir, "session-draft", complete=False)

    html_path = build_index(sessions_dir)
    html = html_path.read_text(encoding="utf-8")
    return sessions_dir, html


# ---------------------------------------------------------------------------
# Output file
# ---------------------------------------------------------------------------


def test_index_html_written(sessions_dir: Path) -> None:
    out = build_index(sessions_dir)
    assert out == sessions_dir / "index.html"
    assert out.exists()


# ---------------------------------------------------------------------------
# Session cards
# ---------------------------------------------------------------------------


def test_session_ids_appear(populated: tuple[Path, str]) -> None:
    _, html = populated
    assert "session-20260101-001" in html
    assert "session-20260314-001" in html


def test_incomplete_session_excluded(populated: tuple[Path, str]) -> None:
    _, html = populated
    assert "session-draft" not in html


def test_dates_appear(populated: tuple[Path, str]) -> None:
    _, html = populated
    assert "2026-01-01" in html
    assert "2026-03-14" in html


def test_duration_appears(populated: tuple[Path, str]) -> None:
    _, html = populated
    # 3723 s = 1:02:03
    assert "1:02:03" in html
    # 5400 s = 1:30:00
    assert "1:30:00" in html


def test_speakers_appear(populated: tuple[Path, str]) -> None:
    _, html = populated
    assert "Alice" in html
    assert "Bob" in html
    assert "GM" in html


def test_links_to_session(populated: tuple[Path, str]) -> None:
    _, html = populated
    assert 'href="session-20260101-001/"' in html
    assert 'href="session-20260314-001/"' in html


# ---------------------------------------------------------------------------
# Ordering — newest first
# ---------------------------------------------------------------------------


def test_newest_first_ordering(populated: tuple[Path, str]) -> None:
    _, html = populated
    pos_new = html.index("session-20260314-001")
    pos_old = html.index("session-20260101-001")
    assert pos_new < pos_old, "Newest session should appear first in HTML"


# ---------------------------------------------------------------------------
# Lunr.js search integration
# ---------------------------------------------------------------------------


def test_lunr_asset_referenced(populated: tuple[Path, str]) -> None:
    _, html = populated
    assert "assets/lunr.min.js" in html
    # No CDN references
    assert "cdn" not in html.lower()
    assert "unpkg" not in html


def test_lunr_asset_copied(populated: tuple[Path, str]) -> None:
    sessions_dir, _ = populated
    assert (sessions_dir / "assets" / "lunr.min.js").exists()


def test_search_docs_json_embedded(populated: tuple[Path, str]) -> None:
    _, html = populated
    # Verify the JSON docs block is present and parseable
    # Extract content between 'var DOCS = ' and the first ';'
    marker = "var DOCS = "
    assert marker in html
    start = html.index(marker) + len(marker)
    end = html.index(";", start)
    docs = json.loads(html[start:end])
    assert isinstance(docs, list)
    assert len(docs) == 2


def test_search_docs_contain_text(populated: tuple[Path, str]) -> None:
    _, html = populated
    marker = "var DOCS = "
    start = html.index(marker) + len(marker)
    end = html.index(";", start)
    docs = json.loads(html[start:end])
    ids = {d["id"] for d in docs}
    assert "session-20260101-001" in ids
    assert "session-20260314-001" in ids
    # body field contains transcript text
    bodies = {d["id"]: d["body"] for d in docs}
    assert "Hello from Alice" in bodies["session-20260101-001"]


# ---------------------------------------------------------------------------
# Empty sessions_dir
# ---------------------------------------------------------------------------


def test_empty_sessions_dir(sessions_dir: Path) -> None:
    html = build_index(sessions_dir).read_text(encoding="utf-8")
    assert "RPG Sessions" in html
    # No cards — just the no-results placeholder and empty DOCS
    assert "var DOCS = []" in html


# ---------------------------------------------------------------------------
# Session without metadata — graceful fallback
# ---------------------------------------------------------------------------


def test_session_without_metadata(sessions_dir: Path) -> None:
    _make_session(
        sessions_dir, "session-20260201-001",
        transcript=[
            {"speaker": "Eve", "start": 0.0, "end": 60.0, "text": "Let's begin."}
        ],
    )
    html = build_index(sessions_dir).read_text(encoding="utf-8")
    assert "session-20260201-001" in html
    assert "Eve" in html
    # Duration derived from transcript end time: 60 s → "1:00"
    assert "1:00" in html


# ---------------------------------------------------------------------------
# Session count in footer
# ---------------------------------------------------------------------------


def test_footer_session_count(populated: tuple[Path, str]) -> None:
    _, html = populated
    assert "2 sessions" in html


def test_footer_singular(sessions_dir: Path) -> None:
    _make_session(sessions_dir, "session-20260101-001", date="2026-01-01")
    html = build_index(sessions_dir).read_text(encoding="utf-8")
    assert "1 session" in html
    assert "1 sessions" not in html
