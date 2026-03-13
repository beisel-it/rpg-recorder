"""
test_html_gen.py — Tests for HTML session player generator (RPGREC-003c).

All tests are pure string/DOM checks — no browser required.

Acceptance criteria verified here:
  - index.html is written to session_dir
  - Speaker labels and colours appear in the output
  - Transcript segments are rendered with data-start / data-end attributes
  - Click-to-seek JS (seekTo / wavesurfer) is present
  - Session metadata (date, duration, participants) is in the output
  - Download links for FLAC files are present
  - Wavesurfer.js is referenced as a local asset (no CDN)
  - Peaks / audio file are injected into the page script when present
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bot.html_gen import generate_session_html


# ---------------------------------------------------------------------------
# Shared sample data
# ---------------------------------------------------------------------------

TRANSCRIPT = [
    {"speaker": "Alice", "start": 0.0,  "end": 3.5,  "text": "Let's roll for initiative."},
    {"speaker": "Bob",   "start": 4.0,  "end": 7.2,  "text": "I got a 17, plus four, so 21."},
    {"speaker": "Alice", "start": 8.1,  "end": 11.3, "text": "The goblin lunges at you."},
    {"speaker": "GM",    "start": 12.0, "end": 15.8, "text": "Roll to hit. Beat a 14."},
]


@pytest.fixture
def session_dir(tmp_path: Path) -> Path:
    d = tmp_path / "session-20260314-001"
    d.mkdir()
    return d


@pytest.fixture
def html(session_dir: Path) -> str:
    """Render index.html with the sample transcript; return its contents."""
    flac_paths = {
        "Alice": session_dir / "alice.flac",
        "Bob":   session_dir / "bob.flac",
    }
    generate_session_html(session_dir, TRANSCRIPT, flac_paths)
    return (session_dir / "index.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Output file
# ---------------------------------------------------------------------------


def test_index_html_is_created(session_dir: Path) -> None:
    """generate_session_html writes index.html to session_dir."""
    generate_session_html(session_dir, TRANSCRIPT, {})
    assert (session_dir / "index.html").exists()


def test_returns_path_to_index_html(session_dir: Path) -> None:
    """Return value is the Path to the generated index.html."""
    result = generate_session_html(session_dir, TRANSCRIPT, {})
    assert result == session_dir / "index.html"


# ---------------------------------------------------------------------------
# Session metadata
# ---------------------------------------------------------------------------


def test_session_id_in_html(html: str, session_dir: Path) -> None:
    assert session_dir.name in html


def test_session_date_in_html(html: str) -> None:
    # Date is rendered as YYYY-MM-DD; just check the year is present.
    assert "2026" in html


def test_duration_in_html(html: str) -> None:
    # Longest end time is 15.8 s → rendered as 0:15.
    assert "0:15" in html


def test_speaker_names_in_html(html: str) -> None:
    for speaker in ("Alice", "Bob", "GM"):
        assert speaker in html


# ---------------------------------------------------------------------------
# Speaker colour-coding
# ---------------------------------------------------------------------------


def test_speaker_colours_applied(html: str) -> None:
    """At least one hex colour from the palette appears in the HTML."""
    # The generator assigns colours like #4fc3f7, #81c784, etc.
    assert "#" in html  # crude check; detailed below
    # Alice gets the first colour (#4fc3f7)
    assert "4fc3f7" in html


def test_three_distinct_speakers_get_distinct_colours(session_dir: Path) -> None:
    """Three speakers → three distinct border-left-color values."""
    generate_session_html(session_dir, TRANSCRIPT, {})
    html = (session_dir / "index.html").read_text()
    # Collect the first three palette entries
    from bot.html_gen import _SPEAKER_COLORS
    colours_used = [c.lstrip("#") for c in _SPEAKER_COLORS[:3]]
    found = sum(1 for c in colours_used if c in html)
    assert found == 3


# ---------------------------------------------------------------------------
# Transcript segments
# ---------------------------------------------------------------------------


def test_all_segment_texts_present(html: str) -> None:
    for seg in TRANSCRIPT:
        assert seg["text"] in html


def test_data_start_attributes_present(html: str) -> None:
    """Each segment has a data-start attribute for JS click-to-seek."""
    for seg in TRANSCRIPT:
        assert f'data-start="{seg["start"]}"' in html


def test_data_end_attributes_present(html: str) -> None:
    for seg in TRANSCRIPT:
        assert f'data-end="{seg["end"]}"' in html


def test_segment_timestamps_formatted(html: str) -> None:
    """Timestamp filter renders seconds as M:SS string."""
    # seg[0] starts at 0.0 → "0:00"
    assert "0:00" in html


# ---------------------------------------------------------------------------
# Download links
# ---------------------------------------------------------------------------


def test_flac_download_links_present(session_dir: Path) -> None:
    flac_paths = {
        "Alice": session_dir / "alice.flac",
        "Bob":   session_dir / "bob.flac",
    }
    generate_session_html(session_dir, TRANSCRIPT, flac_paths)
    html = (session_dir / "index.html").read_text()
    assert "alice.flac" in html
    assert "bob.flac" in html


def test_flac_list_input_works(session_dir: Path) -> None:
    """flac_paths may also be a plain list[Path]."""
    paths = [session_dir / "alice.flac", session_dir / "bob.flac"]
    generate_session_html(session_dir, TRANSCRIPT, paths)
    html = (session_dir / "index.html").read_text()
    assert "alice.flac" in html


def test_mp3_downmix_link_when_present(session_dir: Path) -> None:
    """If downmix.mp3 exists in session_dir, a download link appears."""
    (session_dir / "downmix.mp3").write_bytes(b"fake-mp3")
    generate_session_html(session_dir, TRANSCRIPT, {})
    html = (session_dir / "index.html").read_text()
    assert "downmix.mp3" in html


def test_no_mp3_link_when_absent(html: str) -> None:
    """No downmix file → no MP3 download link in the rendered page."""
    # The fixture session_dir has no downmix file.
    assert "downmix.mp3" not in html


# ---------------------------------------------------------------------------
# Self-hosted assets (no CDN)
# ---------------------------------------------------------------------------


def test_wavesurfer_script_is_local(html: str) -> None:
    """wavesurfer.min.js is loaded from ./assets/, not a CDN."""
    assert "./assets/wavesurfer.min.js" in html


def test_no_cdn_urls_in_html(html: str) -> None:
    """No external CDN hostnames appear in the rendered HTML."""
    cdn_patterns = [
        "cdn.jsdelivr.net",
        "unpkg.com",
        "cdnjs.cloudflare.com",
        "cdn.skypack.dev",
    ]
    for pattern in cdn_patterns:
        assert pattern not in html, f"CDN URL found in HTML: {pattern}"


# ---------------------------------------------------------------------------
# Wavesurfer JS initialisation
# ---------------------------------------------------------------------------


def test_wavesurfer_create_called_in_script(html: str) -> None:
    """WaveSurfer.create() call is present in the page script."""
    assert "WaveSurfer.create" in html


def test_seek_to_present_for_click_handler(html: str) -> None:
    """seekTo is used in the transcript click handler."""
    assert "seekTo" in html


def test_peaks_injected_when_file_present(session_dir: Path) -> None:
    """peaks.json contents are embedded in the page when the file exists."""
    import json
    peaks_data = [0.1, 0.5, 0.3, 0.8]
    (session_dir / "peaks.json").write_text(json.dumps(peaks_data))
    generate_session_html(session_dir, TRANSCRIPT, {})
    html = (session_dir / "index.html").read_text()
    assert "0.5" in html   # peak value visible in the JS


def test_empty_peaks_when_no_file(html: str) -> None:
    """When no peaks.json exists, an empty array is embedded."""
    assert "const PEAKS    = [];" in html


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_transcript(session_dir: Path) -> None:
    """Empty transcript renders without error and produces valid HTML."""
    generate_session_html(session_dir, [], {})
    html = (session_dir / "index.html").read_text()
    assert "<!DOCTYPE html>" in html


def test_html_doctype_present(html: str) -> None:
    assert html.strip().startswith("<!DOCTYPE html>")


def test_assets_dir_created(session_dir: Path) -> None:
    """session_dir/assets/ is created by generate_session_html."""
    generate_session_html(session_dir, TRANSCRIPT, {})
    assert (session_dir / "assets").is_dir()


def test_wavesurfer_vendor_copied_when_exists(session_dir: Path) -> None:
    """wavesurfer.min.js is copied to assets/ if the vendor file exists."""
    generate_session_html(session_dir, TRANSCRIPT, {})
    vendor_src = Path(__file__).parent.parent / "bot" / "vendor" / "wavesurfer.min.js"
    if vendor_src.exists():
        assert (session_dir / "assets" / "wavesurfer.min.js").exists()
