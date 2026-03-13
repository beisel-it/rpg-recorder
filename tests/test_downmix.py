"""
test_downmix.py — Tests for per-speaker downmix / mix-down module (RPGREC-003b).

All tests are skipped until RPGREC-003b is merged.

Acceptance criteria (from RPGREC-003b):
  - downmix(flac_paths) → single mixed-down FLAC at 16 kHz Mono
  - Speaker volumes normalized
  - Output sample rate matches Whisper expectation (16 kHz)
"""

import pytest


@pytest.mark.skip(reason="waiting for RPGREC-003b implementation")
def test_downmix_produces_single_file(sample_flac, tmp_session_dir):
    from bot.downmix import downmix

    result = downmix([sample_flac["5s"]], out_dir=tmp_session_dir)
    assert result.exists()
    assert result.suffix == ".flac"


@pytest.mark.skip(reason="waiting for RPGREC-003b implementation")
def test_downmix_output_is_16khz_mono(sample_flac, tmp_session_dir):
    pass


@pytest.mark.skip(reason="waiting for RPGREC-003b implementation")
def test_downmix_handles_single_speaker(sample_flac, tmp_session_dir):
    pass
