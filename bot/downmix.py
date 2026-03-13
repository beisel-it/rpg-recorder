"""
downmix.py — ffmpeg-based multi-speaker downmix + loudness normalization (RPGREC-003b).

Public API
----------
downmix(flac_paths, out_path, *, target_lufs) -> Path
    Mix per-speaker FLAC files into a single normalized MP3.
    Missing or empty speaker files are skipped with a warning.

Environment variables
---------------------
DOWNMIX_TARGET_LUFS   Target integrated loudness in LUFS (default: -23.0).
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

TARGET_LUFS: float = float(os.getenv("DOWNMIX_TARGET_LUFS", "-23.0"))
_LRA: float = 11.0
_TP: float = -2.0


async def downmix(
    flac_paths: list[Path],
    out_path: Path,
    *,
    target_lufs: float = TARGET_LUFS,
) -> Path:
    """Mix per-speaker FLAC files into a single loudness-normalized MP3.

    Parameters
    ----------
    flac_paths:   Per-speaker FLAC paths to mix (1–8 tracks).
    out_path:     Destination MP3 path (created or overwritten).
    target_lufs:  Target integrated loudness in LUFS (default: -23.0 EBU R128).

    Returns
    -------
    Path to the written MP3 file.

    Raises
    ------
    ValueError   If every supplied path is missing or empty.
    RuntimeError If ffmpeg exits with a non-zero return code.
    """
    valid: list[Path] = []
    for p in flac_paths:
        if not p.exists() or p.stat().st_size == 0:
            log.warning("Skipping %s: missing or empty", p)
        else:
            valid.append(p)

    if not valid:
        raise ValueError("No valid speaker FLAC files to mix — all paths missing or empty")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["ffmpeg", "-y"]
    for p in valid:
        cmd += ["-i", str(p)]

    n = len(valid)
    loudnorm = f"loudnorm=I={target_lufs}:LRA={_LRA}:TP={_TP}"

    if n > 1:
        amix = f"amix=inputs={n}:duration=longest"
        cmd += ["-filter_complex", f"{amix},{loudnorm}"]
    else:
        cmd += ["-af", loudnorm]

    cmd.append(str(out_path))

    log.debug("Running: %s", " ".join(cmd))

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (rc={proc.returncode}): {stderr.decode(errors='replace')}"
        )

    log.info("Downmix complete: %s (%d speaker(s))", out_path, n)
    return out_path
