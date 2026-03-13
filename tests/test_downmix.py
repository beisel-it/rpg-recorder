"""
test_downmix.py — Tests for bot.downmix (RPGREC-003b).

All subprocess calls are mocked — no real ffmpeg required.

Acceptance criteria tested:
  AC1 - 3 speaker tracks -> amix=inputs=3 in ffmpeg filter
  AC2 - loudnorm=I=-23 present in ffmpeg command
  AC3 - returned path matches out_path
  AC4 - 0-byte / missing speaker -> skipped with warning, others still mixed
  AC5 - single valid speaker -> no amix, just loudnorm via -af
  AC6 - all speakers missing -> ValueError, no subprocess spawned
  AC7 - ffmpeg non-zero exit -> RuntimeError propagated
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_proc(returncode: int = 0, stderr: bytes = b"") -> MagicMock:
    """Return a mock asyncio Process with controllable returncode."""
    proc = MagicMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(b"", stderr))
    return proc


def _filter_args(cmd: list) -> list:
    """Extract values of -af and -filter_complex flags from a command list."""
    return [cmd[i + 1] for i, a in enumerate(cmd) if a in ("-af", "-filter_complex")]


# ---------------------------------------------------------------------------
# AC1 + AC2: multi-speaker -> amix + loudnorm in command
# ---------------------------------------------------------------------------


async def test_three_speakers_uses_amix(tmp_path: Path) -> None:
    speakers = []
    for i in range(3):
        p = tmp_path / f"speaker{i}.flac"
        p.write_bytes(b"flac")
        speakers.append(p)
    out = tmp_path / "session_full.mp3"

    with patch("asyncio.create_subprocess_exec", return_value=_make_proc()) as mock_exec:
        from bot.downmix import downmix

        await downmix(speakers, out)

    cmd = list(mock_exec.call_args[0])
    filters = _filter_args(cmd)
    assert any("amix=inputs=3" in f for f in filters), "amix=inputs=3 missing from filter"
    assert any("loudnorm=I=-23" in f for f in filters), "loudnorm=I=-23 missing from filter"


# ---------------------------------------------------------------------------
# AC2: custom LUFS surfaces in command
# ---------------------------------------------------------------------------


async def test_custom_target_lufs_in_command(tmp_path: Path) -> None:
    p = tmp_path / "s.flac"
    p.write_bytes(b"flac")
    out = tmp_path / "out.mp3"

    with patch("asyncio.create_subprocess_exec", return_value=_make_proc()) as mock_exec:
        from bot.downmix import downmix

        await downmix([p], out, target_lufs=-16.0)

    cmd = list(mock_exec.call_args[0])
    filters = _filter_args(cmd)
    assert any("loudnorm=I=-16.0" in f for f in filters)


# ---------------------------------------------------------------------------
# AC3: return value is out_path
# ---------------------------------------------------------------------------


async def test_returns_out_path(tmp_path: Path) -> None:
    p = tmp_path / "s.flac"
    p.write_bytes(b"flac")
    out = tmp_path / "session_full.mp3"

    with patch("asyncio.create_subprocess_exec", return_value=_make_proc()):
        from bot.downmix import downmix

        result = await downmix([p], out)

    assert result == out


# ---------------------------------------------------------------------------
# AC4a: missing file -> skipped, others mixed
# ---------------------------------------------------------------------------


async def test_missing_speaker_skipped(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    import logging

    present = tmp_path / "present.flac"
    present.write_bytes(b"flac")
    missing = tmp_path / "ghost.flac"  # does not exist
    out = tmp_path / "out.mp3"

    with patch("asyncio.create_subprocess_exec", return_value=_make_proc()) as mock_exec:
        from bot.downmix import downmix

        with caplog.at_level(logging.WARNING, logger="bot.downmix"):
            await downmix([present, missing], out)

    cmd = list(mock_exec.call_args[0])
    assert str(missing) not in cmd, "missing file must not appear in ffmpeg inputs"
    assert str(present) in cmd
    assert any("ghost.flac" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# AC4b: 0-byte file -> skipped, others mixed
# ---------------------------------------------------------------------------


async def test_empty_speaker_skipped(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    import logging

    good = tmp_path / "good.flac"
    good.write_bytes(b"flac")
    empty = tmp_path / "empty.flac"
    empty.write_bytes(b"")  # 0 bytes
    out = tmp_path / "out.mp3"

    with patch("asyncio.create_subprocess_exec", return_value=_make_proc()) as mock_exec:
        from bot.downmix import downmix

        with caplog.at_level(logging.WARNING, logger="bot.downmix"):
            await downmix([good, empty], out)

    cmd = list(mock_exec.call_args[0])
    assert str(empty) not in cmd
    assert str(good) in cmd
    assert any("empty.flac" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# AC5: single speaker -> -af loudnorm (no amix)
# ---------------------------------------------------------------------------


async def test_single_speaker_no_amix(tmp_path: Path) -> None:
    p = tmp_path / "solo.flac"
    p.write_bytes(b"flac")
    out = tmp_path / "out.mp3"

    with patch("asyncio.create_subprocess_exec", return_value=_make_proc()) as mock_exec:
        from bot.downmix import downmix

        await downmix([p], out)

    cmd = list(mock_exec.call_args[0])
    filters = _filter_args(cmd)
    assert not any("amix" in f for f in filters), "single speaker must not use amix"
    assert "-af" in cmd
    assert any("loudnorm" in f for f in filters)


# ---------------------------------------------------------------------------
# AC6: all speakers missing -> ValueError, no subprocess
# ---------------------------------------------------------------------------


async def test_all_missing_raises_value_error(tmp_path: Path) -> None:
    ghosts = [tmp_path / f"ghost{i}.flac" for i in range(3)]
    out = tmp_path / "out.mp3"

    with patch("asyncio.create_subprocess_exec", return_value=_make_proc()) as mock_exec:
        from bot.downmix import downmix

        with pytest.raises(ValueError, match="No valid"):
            await downmix(ghosts, out)

    mock_exec.assert_not_called()


# ---------------------------------------------------------------------------
# AC7: ffmpeg failure -> RuntimeError
# ---------------------------------------------------------------------------


async def test_ffmpeg_failure_raises_runtime_error(tmp_path: Path) -> None:
    p = tmp_path / "s.flac"
    p.write_bytes(b"flac")
    out = tmp_path / "out.mp3"

    with patch(
        "asyncio.create_subprocess_exec",
        return_value=_make_proc(returncode=1, stderr=b"codec error"),
    ):
        from bot.downmix import downmix

        with pytest.raises(RuntimeError, match="ffmpeg failed"):
            await downmix([p], out)


# ---------------------------------------------------------------------------
# ffmpeg receives -y flag and correct output path; creates parent dirs
# ---------------------------------------------------------------------------


async def test_ffmpeg_overwrite_flag_and_output_path(tmp_path: Path) -> None:
    p = tmp_path / "s.flac"
    p.write_bytes(b"flac")
    out = tmp_path / "sub" / "session_full.mp3"

    with patch("asyncio.create_subprocess_exec", return_value=_make_proc()) as mock_exec:
        from bot.downmix import downmix

        await downmix([p], out)

    cmd = list(mock_exec.call_args[0])
    assert cmd[0] == "ffmpeg"
    assert "-y" in cmd
    assert cmd[-1] == str(out)
    assert out.parent.exists(), "out_path parent dir must be created"
