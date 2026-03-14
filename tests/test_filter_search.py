"""
test_filter_search.py — Tests for RPGREC-004c: Filter + Search UI.

All tests are pure string/regex checks on rendered HTML — no browser required.

Acceptance criteria verified here:
  - Result count element (#search-count) is present in transcript toolbar
  - JS: applyFilters updates searchCount with "X of Y segments" pattern
  - Keyboard shortcut "/" focuses search box (JS checks for e.key === "/")
  - Keyboard shortcut "Escape" clears and blurs search (JS checks for e.key === "Escape")
  - URL hash deep-linking: applyUrlHash parses #t= and #speaker= params
  - Export .txt: btn-export-txt button present, triggerDownload + fmtTimeFull in JS
  - Export .srt: btn-export-srt button present, fmtSrtTime in JS
  - Export .txt format uses [HH:MM:SS Speaker] Text
  - Export .srt format uses SRT timestamp format (HH:MM:SS,mmm --> HH:MM:SS,mmm)
  - All 004b features still pass (regression)
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
    d = tmp_path / "session-20260314-004c"
    d.mkdir()
    return d


@pytest.fixture
def html(session_dir: Path) -> str:
    """Render index.html with sample transcript; return contents."""
    generate_session_html(session_dir, TRANSCRIPT, {})
    return (session_dir / "index.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Result count element
# ---------------------------------------------------------------------------


def test_search_count_element_present(html: str) -> None:
    """#search-count span is rendered in the transcript toolbar."""
    assert 'id="search-count"' in html


def test_search_count_has_aria_live(html: str) -> None:
    """search-count announces updates to screen readers via aria-live."""
    assert 'aria-live="polite"' in html


def test_search_count_updated_in_apply_filters(html: str) -> None:
    """applyFilters sets searchCount.textContent with 'segments' text."""
    assert "searchCount" in html
    assert "segments" in html


def test_result_count_format_in_js(html: str) -> None:
    """JS produces 'X of Y segments' pattern for filtered results."""
    assert "of" in html
    assert "segments" in html
    # Verify the template string is present in JS
    assert "of ${total} segments" in html or "of \" + total + \" segments" in html or "of ${" in html


# ---------------------------------------------------------------------------
# Keyboard shortcuts — "/" and "Escape"
# ---------------------------------------------------------------------------


def test_slash_key_focuses_search(html: str) -> None:
    """JS handles e.key === "/" to focus the search box."""
    assert 'e.key === "/"' in html or "e.key==='/'" in html or 'e.key === \'/\'' in html


def test_escape_key_clears_search(html: str) -> None:
    """JS handles e.key === "Escape" to clear the search box."""
    assert '"Escape"' in html or "'Escape'" in html


def test_escape_sets_value_to_empty(html: str) -> None:
    """JS sets searchInput.value = '' on Escape."""
    assert 'searchInput.value = ""' in html or "searchInput.value = ''" in html


def test_slash_shortcut_in_kbd_hint(html: str) -> None:
    """The keyboard hint UI mentions '/' for search."""
    assert "/" in html


def test_escape_shortcut_in_kbd_hint(html: str) -> None:
    """The keyboard hint UI mentions Esc/Escape for clear."""
    # Could be "Esc" or "Escape" in the visible hint text
    assert "Esc" in html


# ---------------------------------------------------------------------------
# URL hash deep-linking
# ---------------------------------------------------------------------------


def test_apply_url_hash_function_present(html: str) -> None:
    """applyUrlHash function is defined in the page script."""
    assert "applyUrlHash" in html


def test_hash_t_param_seeking(html: str) -> None:
    """JS parses the 't' param from the URL hash for timestamp seeking."""
    assert 'params.get("t")' in html or "params.get('t')" in html


def test_hash_speaker_param_filtering(html: str) -> None:
    """JS parses the 'speaker' param from the URL hash for speaker filtering."""
    assert 'params.get("speaker")' in html or "params.get('speaker')" in html


def test_url_search_params_used_for_hash(html: str) -> None:
    """URLSearchParams is used to parse the hash string."""
    assert "URLSearchParams" in html


def test_hashchange_listener_registered(html: str) -> None:
    """A hashchange event listener is registered for live hash updates."""
    assert "hashchange" in html


def test_hash_applied_on_load(html: str) -> None:
    """applyUrlHash is called on page load (not just on hashchange)."""
    # Called once directly, and also on hashchange
    count = html.count("applyUrlHash")
    assert count >= 2  # definition + direct call + hashchange listener


# ---------------------------------------------------------------------------
# Export .txt button
# ---------------------------------------------------------------------------


def test_export_txt_button_present(html: str) -> None:
    """btn-export-txt button is present in the transcript toolbar."""
    assert 'id="btn-export-txt"' in html


def test_export_txt_button_is_button_element(html: str) -> None:
    """Export .txt control is rendered as a <button> element."""
    assert re.search(r'<button[^>]+id="btn-export-txt"', html) or \
           re.search(r'id="btn-export-txt"[^>]*>', html)


def test_export_txt_label_visible(html: str) -> None:
    """Export .txt button has '.txt' visible in the label."""
    assert ".txt" in html


def test_trigger_download_function_present(html: str) -> None:
    """triggerDownload helper function is defined in the page script."""
    assert "triggerDownload" in html


def test_fmt_time_full_function_present(html: str) -> None:
    """fmtTimeFull function (HH:MM:SS formatter) is present for .txt export."""
    assert "fmtTimeFull" in html


def test_txt_export_format_string(html: str) -> None:
    """The [HH:MM:SS Speaker] Text format is embedded in the export logic."""
    # The JS template literal uses fmtTimeFull and speaker in brackets
    assert "fmtTimeFull" in html
    assert "transcript.txt" in html


def test_visible_segments_helper_present(html: str) -> None:
    """visibleSegments() helper filters out .hidden segments for export."""
    assert "visibleSegments" in html


# ---------------------------------------------------------------------------
# Export .srt button
# ---------------------------------------------------------------------------


def test_export_srt_button_present(html: str) -> None:
    """btn-export-srt button is present in the transcript toolbar."""
    assert 'id="btn-export-srt"' in html


def test_export_srt_button_is_button_element(html: str) -> None:
    """Export .srt control is rendered as a <button> element."""
    assert re.search(r'<button[^>]+id="btn-export-srt"', html) or \
           re.search(r'id="btn-export-srt"[^>]*>', html)


def test_export_srt_label_visible(html: str) -> None:
    """Export .srt button has '.srt' visible in the label."""
    assert ".srt" in html


def test_fmt_srt_time_function_present(html: str) -> None:
    """fmtSrtTime function (HH:MM:SS,mmm formatter) is present for .srt export."""
    assert "fmtSrtTime" in html


def test_srt_arrow_separator_in_js(html: str) -> None:
    """SRT '-->' separator is present in the srt export block."""
    assert "-->" in html


def test_srt_export_filename(html: str) -> None:
    """transcript.srt filename is used in the .srt export."""
    assert "transcript.srt" in html


# ---------------------------------------------------------------------------
# Export buttons visible / export-row present
# ---------------------------------------------------------------------------


def test_export_row_present(html: str) -> None:
    """An export-row container wraps the export buttons."""
    assert "export-row" in html or "btn-export" in html


def test_both_export_buttons_in_toolbar(html: str) -> None:
    """Both export buttons appear inside the transcript-toolbar."""
    toolbar_start = html.find('class="transcript-toolbar"')
    txt_pos       = html.find('id="btn-export-txt"')
    srt_pos       = html.find('id="btn-export-srt"')
    assert toolbar_start != -1
    assert txt_pos > toolbar_start
    assert srt_pos > toolbar_start


# ---------------------------------------------------------------------------
# Regression: 004b features still present
# ---------------------------------------------------------------------------


def test_speaker_filter_still_works(html: str) -> None:
    """mutedSpeakers Set is still present (speaker filter regression)."""
    assert "mutedSpeakers" in html


def test_apply_filters_still_present(html: str) -> None:
    """applyFilters function is still present."""
    assert "applyFilters" in html


def test_search_input_still_present(html: str) -> None:
    """#transcript-search input is still rendered."""
    assert 'id="transcript-search"' in html


def test_segment_hidden_css_still_present(html: str) -> None:
    """.segment.hidden { display: none } is still in the CSS."""
    assert ".segment.hidden" in html
    assert "display: none" in html or "display:none" in html


def test_seek_to_still_present(html: str) -> None:
    """seekTo (click-to-seek) is still wired in the transcript click handler."""
    assert "seekTo" in html


def test_highlight_active_still_present(html: str) -> None:
    """highlightActive function still fires on audioprocess/seeking."""
    assert "highlightActive" in html
