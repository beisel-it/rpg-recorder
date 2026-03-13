"""
html_gen.py — HTML session player generator (RPGREC-003c).

Public API
----------
generate_session_html(session_dir, transcript, flac_paths) → Path
    Renders templates/session.html.j2 and writes session_dir/index.html.
    Copies wavesurfer.min.js from bot/vendor/ to session_dir/assets/.

Parameters
----------
session_dir : Path
    Output directory for the session.  index.html is written here.
transcript : list[dict]
    [{speaker, start, end, text}, ...] segments sorted by start time.
flac_paths : dict[str, Path] | list[Path]
    Individual FLAC file paths per speaker, used for download links.
    Dict keys are speaker names; list entries use the file stem as the name.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

from jinja2 import Environment, FileSystemLoader, select_autoescape

# ---------------------------------------------------------------------------
# Module-level paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_TEMPLATES_DIR = _HERE.parent / "templates"
_VENDOR_DIR = _HERE / "vendor"

# ---------------------------------------------------------------------------
# Speaker colour palette (dark-mode friendly, high contrast)
# ---------------------------------------------------------------------------

_SPEAKER_COLORS = [
    "#4fc3f7",  # light blue
    "#81c784",  # light green
    "#ffb74d",  # amber
    "#f48fb1",  # pink
    "#ce93d8",  # purple
    "#80cbc4",  # teal
    "#fff176",  # yellow
    "#ff8a65",  # deep orange
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _assign_speaker_colors(transcript: list[dict]) -> dict[str, str]:
    """Return {speaker: colour} in order of first appearance."""
    colours: dict[str, str] = {}
    for seg in transcript:
        spk = seg["speaker"]
        if spk not in colours:
            colours[spk] = _SPEAKER_COLORS[len(colours) % len(_SPEAKER_COLORS)]
    return colours


def _session_duration(transcript: list[dict]) -> float:
    """Return session length in seconds from transcript end times."""
    if not transcript:
        return 0.0
    return max(seg["end"] for seg in transcript)


def _format_duration(seconds: float) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    secs = int(seconds)
    h, remainder = divmod(secs, 3600)
    m, s = divmod(remainder, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_time_filter(seconds: float) -> str:
    """Jinja2 filter: float seconds → 'M:SS' or 'H:MM:SS' string."""
    return _format_duration(seconds)


def _normalise_flac_paths(
    flac_paths: Union[dict[str, Path], list[Path]],
) -> dict[str, Path]:
    if isinstance(flac_paths, dict):
        return flac_paths
    return {Path(p).stem: Path(p) for p in flac_paths}


def _find_downmix(session_dir: Path) -> str | None:
    """Return filename of a downmix audio file if present in session_dir."""
    for candidate in ("downmix.mp3", "session.mp3", "downmix.ogg", "downmix.wav"):
        if (session_dir / candidate).exists():
            return candidate
    return None


def _load_peaks(session_dir: Path) -> list:
    """Load pre-decoded waveform peaks from peaks.json if present."""
    peaks_file = session_dir / "peaks.json"
    if not peaks_file.exists():
        return []
    try:
        return json.loads(peaks_file.read_text())
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_session_html(
    session_dir: Path,
    transcript: list[dict],
    flac_paths: Union[dict[str, Path], list[Path]],
) -> Path:
    """Generate session_dir/index.html from the Jinja2 template.

    Copies bot/vendor/wavesurfer.min.js to session_dir/assets/ so the page
    is fully self-hosted (no CDN requests).

    Returns the path to the generated index.html.
    """
    session_dir = Path(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    # ── Vendor assets ────────────────────────────────────────────────
    assets_dir = session_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    vendor_ws = _VENDOR_DIR / "wavesurfer.min.js"
    if vendor_ws.exists():
        shutil.copy2(vendor_ws, assets_dir / "wavesurfer.min.js")

    # ── Template context ─────────────────────────────────────────────
    speaker_colors = _assign_speaker_colors(transcript)
    speakers = list(speaker_colors.keys())
    duration_secs = _session_duration(transcript)
    flac_dict = _normalise_flac_paths(flac_paths)

    flac_links: list[dict] = [
        {"speaker": spk, "filename": Path(path).name}
        for spk, path in flac_dict.items()
    ]

    # ── Render ───────────────────────────────────────────────────────
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["format_time"] = _format_time_filter

    template = env.get_template("session.html.j2")
    html = template.render(
        session_id=session_dir.name,
        session_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        duration=_format_duration(duration_secs),
        duration_secs=duration_secs,
        speakers=speakers,
        speaker_colors=speaker_colors,
        transcript=transcript,
        peaks_json=json.dumps(_load_peaks(session_dir)),
        audio_file=_find_downmix(session_dir),
        flac_links=flac_links,
    )

    out = session_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
