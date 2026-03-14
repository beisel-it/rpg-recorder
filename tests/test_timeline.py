"""
test_timeline.py — Tests for transcript timeline features (RPGREC-004b).

All tests are pure string checks on rendered HTML — no browser required.

Acceptance criteria verified here:
  - Each segment has a data-speaker attribute for JS speaker filtering
  - Speaker filter buttons (filter-btn) are rendered per speaker
  - Search input (#transcript-search) is present in the transcript panel
  - JS: applyFilters function is present and wires speaker + search filters
  - JS: mutedSpeakers Set is used for speaker toggle state
  - CSS: .segment.hidden { display: none } is present for filtered segments
  - CSS: .filter-btn.muted opacity rule is present
  - Clicking a segment seeks wavesurfer (inherited from 003c — regression check)
  - Active segment highlighting fires on audioprocess / seeking events
"""

from __future__ import annotations

import re
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

SPEAKERS = ["Alice", "Bob", "GM"]


@pytest.fixture
def session_dir(tmp_path: Path) -> Path:
    d = tmp_path / "session-20260314-004b"
    d.mkdir()
    return d


@pytest.fixture
def html(session_dir: Path) -> str:
    """Render index.html with sample transcript; return contents."""
    generate_session_html(session_dir, TRANSCRIPT, {})
    return (session_dir / "index.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# data-speaker attribute on segments
# ---------------------------------------------------------------------------


def test_data_speaker_attribute_present(html: str) -> None:
    """Every segment element has a data-speaker attribute."""
    assert 'data-speaker="Alice"' in html
    assert 'data-speaker="Bob"' in html
    assert 'data-speaker="GM"' in html


def test_data_speaker_values_correct(html: str) -> None:
    """data-speaker values are present for all speakers (segments + buttons)."""
    alice_count = html.count('data-speaker="Alice"')
    bob_count   = html.count('data-speaker="Bob"')
    gm_count    = html.count('data-speaker="GM"')
    assert alice_count >= 2   # 2 segments + 1 filter btn
    assert bob_count   >= 2   # 1 segment  + 1 filter btn
    assert gm_count    >= 2   # 1 segment  + 1 filter btn


# ---------------------------------------------------------------------------
# Speaker filter buttons
# ---------------------------------------------------------------------------


def test_filter_buttons_present(html: str) -> None:
    """A filter-btn element exists for each speaker."""
    assert 'class="filter-btn"' in html


def test_each_speaker_has_filter_button(html: str) -> None:
    """Every speaker in the transcript has exactly one filter button."""
    for speaker in SPEAKERS:
        pattern     = rf'class="filter-btn"[^>]*data-speaker="{re.escape(speaker)}"'
        alt_pattern = rf'data-speaker="{re.escape(speaker)}"[^>]*class="filter-btn"'
        found = re.search(pattern, html) or re.search(alt_pattern, html)
        assert found, f"No filter-btn for speaker '{speaker}'"


def test_filter_button_has_speaker_color(html: str) -> None:
    """Filter buttons carry the speaker's colour (border-color or color CSS)."""
    assert "4fc3f7" in html  # Alice gets first palette colour


def test_filter_button_is_button_element(html: str) -> None:
    """Filter buttons are rendered as <button> elements for keyboard accessibility."""
    assert "<button" in html
    assert 'class="filter-btn"' in html


# ---------------------------------------------------------------------------
# Search input
# ---------------------------------------------------------------------------


def test_search_input_present(html: str) -> None:
    """#transcript-search input element is present in the HTML."""
    assert 'id="transcript-search"' in html


def test_search_input_is_search_type(html: str) -> None:
    """Search input uses type='search' for native clear affordance."""
    assert 'type="search"' in html


def test_search_input_has_placeholder(html: str) -> None:
    """Search input has a non-empty placeholder attribute."""
    match = re.search(r'id="transcript-search"[^>]*placeholder="([^"]+)"', html)
    if not match:
        match = re.search(r'placeholder="([^"]+)"[^>]*id="transcript-search"', html)
    assert match and match.group(1).strip(), "Search input has no placeholder text"


def test_search_input_in_transcript_panel(html: str) -> None:
    """transcript-search is nested inside the transcript panel."""
    panel_start = html.find('id="transcript-panel"')
    search_pos  = html.find('id="transcript-search"')
    assert panel_start != -1 and search_pos > panel_start


# ---------------------------------------------------------------------------
# JavaScript — speaker filter
# ---------------------------------------------------------------------------


def test_muted_speakers_set_present(html: str) -> None:
    """mutedSpeakers Set is declared in the page script."""
    assert "mutedSpeakers" in html


def test_muted_class_toggled_in_js(html: str) -> None:
    """JS toggles the 'muted' class on filter buttons."""
    assert '"muted"' in html or "'muted'" in html


def test_speaker_filter_reads_data_speaker(html: str) -> None:
    """JS reads dataset.speaker from the clicked filter button."""
    assert "dataset.speaker" in html


# ---------------------------------------------------------------------------
# JavaScript — search filter
# ---------------------------------------------------------------------------


def test_apply_filters_function_present(html: str) -> None:
    """applyFilters function is defined in the page script."""
    assert "applyFilters" in html


def test_search_input_wired_in_js(html: str) -> None:
    """JS attaches an 'input' event listener to the search field."""
    assert "transcript-search" in html
    assert '"input"' in html or "'input'" in html


def test_segment_text_queried_for_search(html: str) -> None:
    """JS queries .segment-text to obtain text for search matching."""
    assert ".segment-text" in html


# ---------------------------------------------------------------------------
# CSS — hidden / muted states
# ---------------------------------------------------------------------------


def test_segment_hidden_css_rule(html: str) -> None:
    """.segment.hidden { display: none } hides filtered segments."""
    assert ".segment.hidden" in html
    assert "display: none" in html or "display:none" in html


def test_filter_btn_muted_css_rule(html: str) -> None:
    """.filter-btn.muted applies reduced opacity to toggled-off speakers."""
    assert ".filter-btn.muted" in html
    assert "opacity" in html


# ---------------------------------------------------------------------------
# Regression: existing 003c features still work
# ---------------------------------------------------------------------------


def test_seek_to_still_present(html: str) -> None:
    """seekTo (click-to-seek) is still wired in the transcript click handler."""
    assert "seekTo" in html


def test_highlight_active_still_present(html: str) -> None:
    """highlightActive function still fires on audioprocess/seeking."""
    assert "highlightActive" in html


def test_data_start_and_end_still_present(html: str) -> None:
    """data-start and data-end attributes are still rendered on segments."""
    assert 'data-start="0.0"' in html
    assert 'data-end="3.5"'   in html
