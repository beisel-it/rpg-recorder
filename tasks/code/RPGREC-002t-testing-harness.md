# Task: Testing Harness
Shortcode: RPGREC-002t
Epic: RPGREC-002
Stage: code
Status: ready for code
Priority: P1 ⭐ FIRST TASK — vor allem anderen Code
Assigned: Wilbur
Depends: —
Estimated: 3h

## Warum zuerst?
Jedes Arbeitspaket hat Acceptance Criteria. Ohne automatisierte Tests sind die wertlos. Der Harness muss stehen BEVOR der erste Feature-Code geschrieben wird. Kein Merge ohne grüne Tests.

## Definition of Done

### Test-Infrastruktur
- [ ] pytest als Test-Runner, `pyproject.toml` oder `setup.cfg` konfiguriert
- [ ] `tests/` Verzeichnis mit `conftest.py`
- [ ] `pytest-asyncio` für async Discord-Code
- [ ] `pytest-cov` konfiguriert, Coverage-Report bei jedem Run
- [ ] `make test` oder `scripts/test.sh` als One-Liner zum Ausführen

### Mocks & Fixtures für Discord
- [ ] **`mock_voice_client`** Fixture: Simuliert `VoiceRecvClient` ohne echte Discord-Verbindung
  - `.is_connected()` steuerbar
  - Audio-Callbacks auslösbar (fake PCM-Daten per User-ID)
  - Disconnect-Events simulierbar
- [ ] **`mock_bot`** Fixture: Simuliert `discord.Bot` mit Slash-Command-Dispatch
  - `ctx.author.voice.channel` steuerbar
  - `ctx.respond()` captured für Assertions
- [ ] **`fake_audio`** Fixture: Generiert synthetische PCM-Daten
  - Konfigurierbar: Dauer, Sample-Rate (48kHz), Channels (Mono/Stereo)
  - Deterministic (Seed-basiert) für reproduzierbare Tests
  - Stille + Ton wechselnd (für VAD-Tests)

### Fixtures für Pipeline
- [ ] **`sample_flac`** Fixture: Kurze .flac Dateien (5s, 30s) mit bekanntem Inhalt
  - Generiert via `soundfile` oder mitgeliefert als Testdaten
- [ ] **`sample_transcript`** Fixture: Bekanntes JSON `[{speaker, start, end, text}]`
- [ ] **`tmp_session_dir`** Fixture: Temporäres Output-Verzeichnis (pytest `tmp_path`)

### Smoke Tests (als Vorlage für Feature-Tests)
- [ ] `test_config.py`: Config lädt .env, fehlende Pflichtfelder → ValueError
- [ ] `test_chunked_sink.py`: Platzhalter mit `@pytest.mark.skip("waiting for 002c")`
- [ ] `test_whisper.py`: Platzhalter mit Skip
- [ ] `test_downmix.py`: Platzhalter mit Skip
- [ ] `test_pipeline.py`: Platzhalter mit Skip

### CI-Integration
- [ ] GitHub Actions Workflow: `.github/workflows/test.yml`
  - Trigger: Push + PR auf main
  - Python 3.11, pip install, pytest
  - Coverage-Report als Artifact
  - **Fail on <80% Coverage** (für neuen Code)
- [ ] Branch-Protection: PRs müssen grüne CI haben (empfohlen, nicht blocking für diesen Task)

### Test-Konventionen (CONTRIBUTING.md oder tests/README.md)
- [ ] Jeder neue Task MUSS Tests mitbringen die seine Acceptance Criteria automatisiert prüfen
- [ ] Naming: `test_<feature>_<scenario>.py` → `test_chunked_sink_creates_chunks.py`
- [ ] Kein Merge ohne grüne Tests — das ist die Regel, keine Empfehlung

## Acceptance Criteria
1. `make test` → pytest findet Tests, alle grün (Platzhalter-Skips ok)
2. `mock_voice_client` Fixture: `vc.is_connected()` → True/False steuerbar
3. `fake_audio(duration=5)` → gibt 5s PCM-Daten zurück (48kHz, 16-bit, Mono = 480.000 Bytes)
4. GitHub Actions: Push auf main → CI läuft, Coverage-Report sichtbar
5. `tests/README.md` beschreibt Konventionen + wie man Fixtures nutzt

## File Structure

```
tests/
├── README.md              # Test-Konventionen
├── conftest.py            # Shared Fixtures
├── fixtures/
│   ├── audio/             # Sample .flac / .wav Dateien
│   └── transcripts/       # Sample .json Transkripte
├── mocks/
│   ├── __init__.py
│   ├── discord_mocks.py   # mock_voice_client, mock_bot
│   └── audio_mocks.py     # fake_audio Generator
├── test_config.py         # Config-Loading Tests
├── test_chunked_sink.py   # (Platzhalter für 002c)
├── test_whisper.py        # (Platzhalter für 003a)
├── test_downmix.py        # (Platzhalter für 003b)
└── test_pipeline.py       # (Platzhalter für 003d)
```

## Regel für alle nachfolgenden Tasks

**Kein Task ist "done" ohne:**
1. Tests die seine Acceptance Criteria automatisiert prüfen
2. Bestehende Tests weiterhin grün
3. Coverage des neuen Codes ≥80%

Diese Regel wird in `tests/README.md` dokumentiert und gilt ab sofort.

## Comments
- MUSS der erste Task sein den Wilbur implementiert
- Ohne das wird jeder nachfolgende Task "tested by vibes"
- Branch: `feature/RPGREC-002t-testing`
- Erstellt von Nova (Researcher) 2026-03-13, auf Florians Anweisung
