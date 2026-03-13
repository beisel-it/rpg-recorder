# rpg-recorder — Test Conventions

## Running Tests

```bash
make test            # Full suite with coverage report
./scripts/test.sh    # Same, scriptable
pytest -p no:cov -q  # Fast run, no coverage (dev loop)
pytest -k test_config  # Run a specific test subset
```

`DISCORD_TOKEN` is automatically set to a dummy value by `scripts/test.sh` and
the Makefile so the bot config module won't fail on import during testing.

---

## Directory Layout

```
tests/
├── README.md                    # ← you are here
├── conftest.py                  # Shared fixtures (auto-loaded by pytest)
├── fixtures/
│   ├── audio/                   # .wav / .flac sample files
│   └── transcripts/
│       └── sample.json          # Known [{speaker, start, end, text}]
├── mocks/
│   ├── __init__.py
│   ├── discord_mocks.py         # MockVoiceClient, MockBot, MockInteraction
│   └── audio_mocks.py           # generate_fake_audio()
├── test_config.py               # bot.config loading ✅
├── test_chunked_sink.py         # ChunkedFileSink (skipped — 002c)
├── test_whisper.py              # Whisper transcription (skipped — 003a)
├── test_downmix.py              # Downmix pipeline (skipped — 003b)
└── test_pipeline.py             # End-to-end pipeline (skipped — 003d)
```

---

## Available Fixtures

| Fixture | Type | Purpose |
|---|---|---|
| `mock_voice_client` | `MockVoiceClient` | Fake `VoiceRecvClient` — `is_connected()` controllable, `fire_audio()` triggers the sink |
| `mock_bot` | `MockBot` | Fake `discord.Bot` for cog registration tests |
| `fake_audio` | `Callable[..., bytes]` | Generates synthetic 48 kHz 16-bit PCM |
| `sample_flac` | `dict[str, Path]` | `{"5s": Path, "30s": Path}` — tiny WAV files with known content |
| `sample_transcript` | `tuple[list[dict], Path]` | Known transcript entries + path to JSON file |
| `tmp_session_dir` | `Path` | Temp session dir with `chunks/` sub-dir (auto-cleaned by pytest) |

### `mock_voice_client`

```python
def test_connected_state(mock_voice_client):
    assert mock_voice_client.is_connected()   # starts True

    mock_voice_client.set_connected(False)
    assert not mock_voice_client.is_connected()

def test_audio_callback(mock_voice_client, tmp_session_dir, fake_audio):
    from bot.recorder import ChunkedFileSink
    from tests.mocks.discord_mocks import MockUser

    sink = ChunkedFileSink(tmp_session_dir / "chunks")
    mock_voice_client.listen(sink)

    user = MockUser(user_id=42, name="Gandalf")
    mock_voice_client.fire_audio(user, fake_audio(duration=1))

    assert sink.speaker_count() == 1
    sink.cleanup()
```

### `fake_audio`

```python
def test_pcm_length(fake_audio):
    # 5 s × 48 000 Hz × 2 bytes × 1 channel = 480 000 bytes
    pcm = fake_audio(duration=5)
    assert len(pcm) == 480_000

def test_stereo(fake_audio):
    pcm = fake_audio(duration=1, channels=2)
    assert len(pcm) == 192_000   # 48 000 × 2 bytes × 2 ch × 1 s
```

### `sample_transcript`

```python
def test_transcript_structure(sample_transcript):
    entries, path = sample_transcript
    assert len(entries) > 0
    assert all({"speaker", "start", "end", "text"}.issubset(e) for e in entries)
    assert path.exists()
```

---

## Naming Convention

```
test_<feature>_<scenario>.py          # file
test_<feature>_<scenario>             # function / method
```

Examples:
- `test_chunked_sink_creates_chunks.py`
- `test_chunked_sink_rolls_over_at_chunk_limit`
- `test_whisper_empty_audio_returns_empty_list`

---

## The Rule — No Merge Without Tests

> **Every task that ships code MUST include tests that automatically verify its
> Acceptance Criteria.**

Checklist before opening a PR:

1. New Acceptance Criteria have matching `test_` functions that pass
2. All previously-passing tests still pass (`make test` is green)
3. Coverage of new code ≥ 80 % (CI enforces this)

CI will fail the build on coverage < 80 %. There is no override.
This rule is non-negotiable: *no green CI, no merge.*

---

## Async Tests

`pytest-asyncio` is configured with `asyncio_mode = "auto"` — async test
functions are detected automatically.

```python
async def test_something_async():
    result = await some_coroutine()
    assert result == expected
```

No `@pytest.mark.asyncio` decorator needed.

---

## Adding New Test Files

1. Create `tests/test_<feature>.py`
2. Import only from `bot.*` and `tests.mocks.*`
3. Use fixtures from `conftest.py` — do not re-create them locally
4. Skip tests for unimplemented features with:
   ```python
   @pytest.mark.skip(reason="waiting for RPGREC-00Xx implementation")
   ```
5. Remove the skip and write the real body when the feature ships
