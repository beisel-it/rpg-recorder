"""
audio_mocks.py — Synthetic PCM generator for testing without real audio files.

Usage:
    from tests.mocks.audio_mocks import generate_fake_audio

    pcm = generate_fake_audio(duration=5)
    # → 480 000 bytes  (48 kHz, 16-bit, Mono, 5 s)

    pcm = generate_fake_audio(duration=2, channels=2, seed=42)
    # → 384 000 bytes  (48 kHz, 16-bit, Stereo, 2 s)

The generated signal alternates between silence and a 440 Hz sine tone
every 0.5 s, giving VAD-style tests a realistic input.
"""

from __future__ import annotations

import math
import struct


SAMPLE_RATE = 48_000   # Hz — Discord native rate
SAMPLE_WIDTH = 2       # bytes — 16-bit signed LE


def generate_fake_audio(
    duration: float = 1.0,
    sample_rate: int = SAMPLE_RATE,
    channels: int = 1,
    seed: int = 0,
    tone_hz: float = 440.0,
    silence_interval: float = 0.5,
) -> bytes:
    """Return deterministic raw PCM bytes.

    Parameters
    ----------
    duration:         Total length in seconds.
    sample_rate:      Samples per second (default 48 000).
    channels:         1 = Mono, 2 = Stereo.
    seed:             Changes amplitude offset for determinism across test runs.
    tone_hz:          Frequency of the sine-wave "speech" segment.
    silence_interval: Length (seconds) of each silence/tone alternation cycle.
    """
    n_samples = int(duration * sample_rate)
    amplitude = 16000 + (seed % 1000)   # sub-maximum to avoid clipping
    samples_per_interval = int(silence_interval * sample_rate)

    frames: list[bytes] = []
    for i in range(n_samples):
        # Alternate silence / tone every silence_interval seconds
        interval_index = i // samples_per_interval
        if interval_index % 2 == 0:
            value = 0
        else:
            t = i / sample_rate
            value = int(amplitude * math.sin(2 * math.pi * tone_hz * t))

        sample = struct.pack("<h", value)
        frames.append(sample * channels)

    return b"".join(frames)


def expected_byte_count(
    duration: float,
    sample_rate: int = SAMPLE_RATE,
    channels: int = 1,
) -> int:
    """Return the exact byte count for given parameters (useful in assertions)."""
    return int(duration * sample_rate) * SAMPLE_WIDTH * channels
