"""
test_whisper.py — Tests for Whisper transcription module (RPGREC-003a).

All tests are skipped until RPGREC-003a is merged.

Acceptance criteria (from RPGREC-003a):
  - transcribe(flac_path) → list[{speaker, start, end, text}]
  - Handles empty/short files gracefully (returns [])
  - Respects configured model size
"""

import pytest


@pytest.mark.skip(reason="waiting for RPGREC-003a implementation")
def test_whisper_transcribes_sample(sample_flac):
    from bot.transcribe import transcribe

    result = transcribe(sample_flac["5s"])
    assert isinstance(result, list)
    for entry in result:
        assert {"speaker", "start", "end", "text"}.issubset(entry.keys())


@pytest.mark.skip(reason="waiting for RPGREC-003a implementation")
def test_whisper_empty_audio_returns_empty_list(sample_flac):
    pass


@pytest.mark.skip(reason="waiting for RPGREC-003a implementation")
def test_whisper_respects_model_config(sample_flac, monkeypatch):
    pass
