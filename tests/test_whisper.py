"""
test_whisper.py — Tests for Whisper transcription module (RPGREC-003a).

All tests use mocks — no GPU or real Whisper model required in CI.

Acceptance criteria (from RPGREC-003a):
  - transcribe(flac_path) → list[{speaker, start, end, text, confidence}]
  - Audio split into ≤10-min chunks (prevents hallucinations)
  - vad_filter=True and condition_on_previous_text=False always passed
  - initial_prompt forwarded from WHISPER_INITIAL_PROMPT env var
  - Handles empty / zero-byte files gracefully (returns [])
  - Model name configurable via WHISPER_MODEL env var
  - Per-speaker error in transcribe_session → error logged, others continue
  - Timeout per speaker → returns [] for timed-out speaker
"""

from __future__ import annotations

import concurrent.futures
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import wave

import pytest


# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------


def _make_segment(start: float, end: float, text: str, avg_logprob: float = -0.3):
    """Build a MagicMock that looks like a faster-whisper Segment."""
    seg = MagicMock()
    seg.start = start
    seg.end = end
    seg.text = text
    seg.avg_logprob = avg_logprob
    return seg


def _mock_model(*segments):
    """Return a MagicMock WhisperModel whose .transcribe() yields *segments*."""
    model = MagicMock()
    model.transcribe.return_value = (iter(segments), MagicMock())
    return model


# ---------------------------------------------------------------------------
# transcribe() — basic output contract
# ---------------------------------------------------------------------------


def test_whisper_transcribes_sample(sample_flac, monkeypatch):
    """transcribe() returns a list of properly-shaped dicts for a valid WAV."""
    from bot.transcribe import transcribe

    seg = _make_segment(0.0, 1.5, "Thalindra greift an.")
    mock_model = _mock_model(seg)
    monkeypatch.setattr("bot.transcribe._get_model", lambda: mock_model)

    result = transcribe(sample_flac["5s"])

    assert isinstance(result, list)
    assert len(result) == 1
    entry = result[0]
    assert {"speaker", "start", "end", "text", "confidence"}.issubset(entry.keys())
    assert entry["speaker"] == "unknown"
    assert entry["text"] == "Thalindra greift an."
    assert entry["start"] == pytest.approx(0.0)
    assert entry["end"] == pytest.approx(1.5)


def test_whisper_output_sorted_by_start(sample_flac, monkeypatch):
    """Segments are returned sorted by start time regardless of model order."""
    from bot.transcribe import transcribe

    # Intentionally out of order
    segs = [
        _make_segment(5.0, 6.0, "Second."),
        _make_segment(1.0, 2.0, "First."),
        _make_segment(3.0, 4.0, "Middle."),
    ]
    monkeypatch.setattr("bot.transcribe._get_model", lambda: _mock_model(*segs))

    result = transcribe(sample_flac["5s"])

    starts = [e["start"] for e in result]
    assert starts == sorted(starts)


def test_whisper_speaker_label_embedded(sample_flac, monkeypatch):
    """Speaker label passed to transcribe() appears in every output entry."""
    from bot.transcribe import transcribe

    seg = _make_segment(0.0, 1.0, "Grimjaw brüllt.")
    monkeypatch.setattr("bot.transcribe._get_model", lambda: _mock_model(seg))

    result = transcribe(sample_flac["5s"], speaker="Grimjaw")

    assert all(e["speaker"] == "Grimjaw" for e in result)


# ---------------------------------------------------------------------------
# Empty / corrupt input
# ---------------------------------------------------------------------------


def test_whisper_empty_audio_returns_empty_list(tmp_path, monkeypatch):
    """Zero-byte file → empty list, no exception."""
    from bot.transcribe import transcribe

    empty_file = tmp_path / "empty.flac"
    empty_file.write_bytes(b"")

    # _get_model should never be called for an empty file
    mock_model = MagicMock()
    monkeypatch.setattr("bot.transcribe._get_model", lambda: mock_model)

    result = transcribe(empty_file)

    assert result == []
    mock_model.transcribe.assert_not_called()


def test_whisper_missing_file_returns_empty_list(tmp_path, monkeypatch):
    """Non-existent file → empty list, no exception."""
    from bot.transcribe import transcribe

    monkeypatch.setattr("bot.transcribe._get_model", lambda: MagicMock())

    result = transcribe(tmp_path / "does_not_exist.flac")

    assert result == []


def test_whisper_whitespace_only_segments_filtered(sample_flac, monkeypatch):
    """Segments whose text is purely whitespace are dropped from the output."""
    from bot.transcribe import transcribe

    segs = [
        _make_segment(0.0, 1.0, "   "),   # whitespace only → filtered
        _make_segment(1.0, 2.0, "Real text."),
    ]
    monkeypatch.setattr("bot.transcribe._get_model", lambda: _mock_model(*segs))

    result = transcribe(sample_flac["5s"])

    assert len(result) == 1
    assert result[0]["text"] == "Real text."


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------


def test_whisper_respects_model_config(sample_flac, monkeypatch):
    """WHISPER_MODEL env var is forwarded to WhisperModel constructor."""
    monkeypatch.setenv("WHISPER_MODEL", "large-v2")

    import importlib
    import bot.transcribe as transcribe_mod
    importlib.reload(transcribe_mod)

    try:
        assert transcribe_mod.WHISPER_MODEL == "large-v2"
    finally:
        # Restore default after test
        monkeypatch.delenv("WHISPER_MODEL", raising=False)
        importlib.reload(transcribe_mod)


def test_whisper_default_model_is_large_v3_turbo(monkeypatch):
    """Default model is large-v3-turbo when env var is not set."""
    monkeypatch.delenv("WHISPER_MODEL", raising=False)

    import importlib
    import bot.transcribe as transcribe_mod
    importlib.reload(transcribe_mod)

    assert transcribe_mod.WHISPER_MODEL == "large-v3-turbo"


# ---------------------------------------------------------------------------
# initial_prompt
# ---------------------------------------------------------------------------


def test_whisper_initial_prompt_forwarded(sample_flac, monkeypatch):
    """WHISPER_INITIAL_PROMPT is passed through to model.transcribe()."""
    from bot.transcribe import transcribe

    prompt = "Thalindra, Grimjaw, Mondscheinwald"
    monkeypatch.setattr("bot.transcribe.WHISPER_INITIAL_PROMPT", prompt)

    seg = _make_segment(0.0, 1.0, "Sie betritt den Mondscheinwald.")
    mock_model = _mock_model(seg)
    monkeypatch.setattr("bot.transcribe._get_model", lambda: mock_model)

    transcribe(sample_flac["5s"])

    _args, kwargs = mock_model.transcribe.call_args
    assert kwargs.get("initial_prompt") == prompt


def test_whisper_vad_and_no_condition_always_set(sample_flac, monkeypatch):
    """vad_filter=True and condition_on_previous_text=False are always passed."""
    from bot.transcribe import transcribe

    mock_model = _mock_model(_make_segment(0.0, 1.0, "Test."))
    monkeypatch.setattr("bot.transcribe._get_model", lambda: mock_model)

    transcribe(sample_flac["5s"])

    _args, kwargs = mock_model.transcribe.call_args
    assert kwargs.get("vad_filter") is True
    assert kwargs.get("condition_on_previous_text") is False


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def test_whisper_long_audio_split_into_chunks(tmp_path, monkeypatch):
    """Audio longer than CHUNK_SECONDS is split; model.transcribe called once per chunk."""
    import bot.transcribe as transcribe_mod
    from bot.transcribe import transcribe
    import sys

    # Patch CHUNK_SECONDS small enough that our fake audio triggers 3 chunks
    SAMPLE_RATE = 10
    monkeypatch.setattr(transcribe_mod, "CHUNK_SECONDS", 1)  # 1s chunks

    # Return a 3-second fake audio (30 samples at rate=10) → 3 chunks
    class _LongAudio:
        ndim = 1
        size = 30  # 3 seconds * 10 samples/s
        shape = (30,)
        dtype = "float32"
        def __len__(self): return self.size
        def mean(self, axis=None): return self
        def __getitem__(self, key):
            sliced = _LongAudio()
            if isinstance(key, slice):
                start_ = key.start or 0
                stop_ = min(key.stop or self.size, self.size)
                sliced.size = max(0, stop_ - start_)
                sliced.shape = (sliced.size,)
            return sliced

    sys.modules["soundfile"].read = MagicMock(return_value=(_LongAudio(), SAMPLE_RATE))

    call_count = 0
    seg = MagicMock(); seg.start = 0.0; seg.end = 0.5; seg.text = "hi"
    mock_model = _mock_model(seg)
    original_transcribe = mock_model.transcribe

    def counting_transcribe(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_transcribe(*args, **kwargs)

    mock_model.transcribe = counting_transcribe
    monkeypatch.setattr(transcribe_mod, "_get_model", lambda: mock_model)

    wav_path = tmp_path / "long.wav"
    wav_path.write_bytes(b"fake")
    transcribe(wav_path, model=mock_model)

    # 30 samples / 10 samples per second = 3 seconds / 1s per chunk = 3 calls
    assert call_count == 3


# ---------------------------------------------------------------------------
# Timeout handling
# ---------------------------------------------------------------------------


def test_whisper_timeout_returns_empty_list(sample_flac, monkeypatch):
    """When transcription times out, transcribe() returns [] and logs an error."""
    import bot.transcribe as transcribe_mod
    from bot.transcribe import transcribe

    def slow_transcribe(*args, **kwargs):
        import time
        time.sleep(10)
        return []

    monkeypatch.setattr(transcribe_mod, "_transcribe_chunks", slow_transcribe)
    monkeypatch.setattr(transcribe_mod, "_get_model", lambda: MagicMock())

    result = transcribe(sample_flac["5s"], timeout=0.01)

    assert result == []


# ---------------------------------------------------------------------------
# transcribe_session() — multi-speaker orchestration
# ---------------------------------------------------------------------------


def test_transcribe_session_merges_and_sorts(sample_flac, monkeypatch):
    """transcribe_session() merges segments from all speakers, sorted by start."""
    import bot.transcribe as transcribe_mod

    alice_entries = [
        {"speaker": "Alice", "start": 2.0, "end": 3.0, "text": "Ich greife an.", "confidence": -0.3},
    ]
    bob_entries = [
        {"speaker": "Bob", "start": 0.5, "end": 1.5, "text": "Ich verteidige.", "confidence": -0.4},
        {"speaker": "Bob", "start": 4.0, "end": 5.0, "text": "Treffer!", "confidence": -0.2},
    ]

    call_map: dict[str, list[dict]] = {
        "Alice": alice_entries,
        "Bob": bob_entries,
    }

    def fake_transcribe(path, speaker, *, model, timeout):
        return call_map[speaker]

    monkeypatch.setattr(transcribe_mod, "transcribe", fake_transcribe)
    monkeypatch.setattr(transcribe_mod, "_get_model", lambda: MagicMock())

    from bot.transcribe import transcribe_session

    result = transcribe_session(
        {"Alice": sample_flac["5s"], "Bob": sample_flac["30s"]}
    )

    assert len(result) == 3
    starts = [e["start"] for e in result]
    assert starts == sorted(starts)
    speakers = [e["speaker"] for e in result]
    assert "Alice" in speakers and "Bob" in speakers


def test_transcribe_session_continues_on_speaker_error(sample_flac, monkeypatch, caplog):
    """One speaker raising an exception → error logged, other speakers succeed."""
    import logging
    import bot.transcribe as transcribe_mod

    def fake_transcribe(path, speaker, *, model, timeout):
        if speaker == "Broken":
            raise RuntimeError("GPU exploded")
        return [{"speaker": speaker, "start": 0.0, "end": 1.0, "text": "OK.", "confidence": -0.3}]

    monkeypatch.setattr(transcribe_mod, "transcribe", fake_transcribe)
    monkeypatch.setattr(transcribe_mod, "_get_model", lambda: MagicMock())

    from bot.transcribe import transcribe_session

    with caplog.at_level(logging.ERROR, logger="bot.transcribe"):
        result = transcribe_session(
            {"Broken": sample_flac["5s"], "Fine": sample_flac["30s"]}
        )

    # Fine speaker's segment should still be returned
    assert len(result) == 1
    assert result[0]["speaker"] == "Fine"

    # Error should be logged
    assert any("Broken" in rec.message for rec in caplog.records)


def test_transcribe_session_empty_dict_returns_empty(monkeypatch):
    """Empty speaker_files dict → empty list."""
    import bot.transcribe as transcribe_mod
    monkeypatch.setattr(transcribe_mod, "_get_model", lambda: MagicMock())

    from bot.transcribe import transcribe_session

    result = transcribe_session({})
    assert result == []


# ---------------------------------------------------------------------------
# _get_model integration (uses patched WhisperModel)
# ---------------------------------------------------------------------------


def test_get_model_uses_whisper_model_env(monkeypatch):
    """_get_model() passes WHISPER_MODEL to WhisperModel constructor."""
    import bot.transcribe as transcribe_mod
    monkeypatch.setattr(transcribe_mod, "WHISPER_MODEL", "tiny")

    mock_cls = MagicMock(return_value=MagicMock())
    # Patch inside the function's import scope, not the top-level module
    with patch.dict("sys.modules", {"faster_whisper": MagicMock(WhisperModel=mock_cls)}):
        transcribe_mod._get_model()

    mock_cls.assert_called_once_with("tiny", device="auto", compute_type="auto")
