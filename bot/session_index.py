"""
session_index.py — Session index page generator (RPGREC-009).

Public API
----------
build_index(sessions_dir) → Path
    Scan sessions_dir for completed session sub-directories, then render
    sessions_dir/index.html — a static page with session cards and Lunr.js
    full-text search across all transcripts.

    Returns the path to the written index.html.

A session directory is recognised as complete when it contains index.html.
Metadata is read from (in order of preference):
  1. metadata.json  {"date": "YYYY-MM-DD", "duration_seconds": N}
  2. transcript.json [{speaker, start, end, text}, …]
  3. The directory name itself (as a fallback for date/id).
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# ---------------------------------------------------------------------------
# Module-level paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_TEMPLATES_DIR = _HERE.parent / "templates"
_VENDOR_DIR = _HERE / "vendor"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> Any:
    """Read and parse a JSON file; return None on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _format_duration(seconds: float) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    secs = int(seconds)
    h, remainder = divmod(secs, 3600)
    m, s = divmod(remainder, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _collect_session(session_dir: Path) -> dict | None:
    """
    Extract display metadata + search text for one session directory.

    Returns None if the directory does not look like a completed session
    (i.e. it has no index.html).
    """
    if not (session_dir / "index.html").exists():
        return None

    session_id = session_dir.name

    # ── metadata.json ────────────────────────────────────────────────
    meta = _read_json(session_dir / "metadata.json") or {}
    date_str: str = meta.get("date", "")
    duration_secs: float = float(meta.get("duration_seconds", 0.0))

    # ── transcript.json ───────────────────────────────────────────────
    transcript: list[dict] = _read_json(session_dir / "transcript.json") or []
    speakers: list[str] = []
    seen: set[str] = set()
    full_text_parts: list[str] = []
    for seg in transcript:
        spk = seg.get("speaker", "")
        if spk and spk not in seen:
            speakers.append(spk)
            seen.add(spk)
        text = seg.get("text", "")
        if text:
            full_text_parts.append(text)

    # Derive duration from transcript when metadata is missing
    if not duration_secs and transcript:
        duration_secs = max(seg.get("end", 0.0) for seg in transcript)

    # Derive date from directory name when metadata is missing
    if not date_str:
        # Typical format: session-20260314-001 or 2026-03-14-...
        parts = session_id.replace("session-", "").split("-")
        if len(parts) >= 3:
            candidate = "-".join(parts[:3])
            # Try YYYYMMDD style (e.g. 20260314)
            if len(parts[0]) == 8 and parts[0].isdigit():
                raw = parts[0]
                candidate = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
            try:
                datetime.strptime(candidate, "%Y-%m-%d")
                date_str = candidate
            except ValueError:
                pass

    # Sort key: ISO date descending, then session_id
    sort_key = date_str or session_id

    return {
        "id": session_id,
        "date": date_str or session_id,
        "duration": _format_duration(duration_secs),
        "speakers": speakers,
        "link": f"{session_id}/",
        "full_text": " ".join(full_text_parts),
        "_sort_key": sort_key,
    }


def _gather_sessions(sessions_dir: Path) -> list[dict]:
    """Return session metadata dicts sorted newest-first."""
    sessions: list[dict] = []
    for entry in sorted(sessions_dir.iterdir()):
        if not entry.is_dir():
            continue
        info = _collect_session(entry)
        if info:
            sessions.append(info)
    # Newest first
    sessions.sort(key=lambda s: s["_sort_key"], reverse=True)
    return sessions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_index(sessions_dir: Path) -> Path:
    """Render sessions_dir/index.html — a session cards + Lunr.js search page.

    Parameters
    ----------
    sessions_dir:
        Root directory containing per-session sub-directories.

    Returns
    -------
    Path to the written index.html.
    """
    sessions_dir = Path(sessions_dir)

    # ── Vendor assets ────────────────────────────────────────────────
    assets_dir = sessions_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    lunr_src = _VENDOR_DIR / "lunr.min.js"
    if lunr_src.exists():
        shutil.copy2(lunr_src, assets_dir / "lunr.min.js")

    # ── Gather sessions ───────────────────────────────────────────────
    sessions = _gather_sessions(sessions_dir)

    # ── Build Lunr search index ───────────────────────────────────────
    # Embed the documents as JSON; JS side builds the index on page load.
    search_docs = [
        {
            "id": s["id"],
            "date": s["date"],
            "speakers": " ".join(s["speakers"]),
            "body": s["full_text"],
        }
        for s in sessions
    ]

    # Strip internal keys before passing to template
    display_sessions = [
        {k: v for k, v in s.items() if not k.startswith("_")}
        for s in sessions
    ]

    # ── Render ───────────────────────────────────────────────────────
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("index.html.j2")
    html = template.render(
        sessions=display_sessions,
        search_docs_json=json.dumps(search_docs, ensure_ascii=False),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    out = sessions_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
