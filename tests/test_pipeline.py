"""
test_pipeline.py — End-to-end pipeline tests (RPGREC-003d).

All tests are skipped until RPGREC-003d is merged.

Acceptance criteria (from RPGREC-003d):
  - run_pipeline(session_dir) → produces metadata.json + transcript.json + HTML
  - Pipeline is idempotent: running twice does not duplicate output
  - Handles partial sessions (no audio for some speakers)
"""

import pytest


@pytest.mark.skip(reason="waiting for RPGREC-003d implementation")
async def test_pipeline_produces_transcript(tmp_session_dir, sample_flac):
    from bot.pipeline import run_pipeline

    # Seed the session dir with sample audio
    (tmp_session_dir / "chunks").mkdir(exist_ok=True)

    result = await run_pipeline(tmp_session_dir)
    assert (tmp_session_dir / "transcript.json").exists()
    assert isinstance(result["speakers"], list)


@pytest.mark.skip(reason="waiting for RPGREC-003d implementation")
async def test_pipeline_is_idempotent(tmp_session_dir, sample_flac):
    pass


@pytest.mark.skip(reason="waiting for RPGREC-003d implementation")
async def test_pipeline_handles_empty_session(tmp_session_dir):
    pass


@pytest.mark.skip(reason="waiting for RPGREC-003d implementation")
async def test_pipeline_produces_html(tmp_session_dir, sample_flac, sample_transcript):
    pass
