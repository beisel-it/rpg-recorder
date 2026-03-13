# Tech Stack Research — RPG Recorder

**RPGREC-001** | Researcher: Nova 🔭 | Datum: 2026-03-13

---

## 1. discord-ext-voice-receive

### Übersicht

| Aspekt | Bewertung |
|--------|-----------|
| **Package** | `discord-ext-voice-recv` (PyPI) |
| **GitHub** | imayhaveborkedit/discord-ext-voice-recv |
| **Version** | 0.4.2a145 (Alpha!) |
| **Python** | ≥3.8, empfohlen 3.11+ |
| **Dependency** | discord.py mit Voice-Support (pynacl) |
| **Lizenz** | MIT |
| **Stars** | ~172 |

### Stabilität

**⚠️ Alpha-Software — der Autor sagt es selbst:**
> "No guarantees are given for stability or random breaking changes."

Das ist die **einzige** Option für Voice Receive mit discord.py. Es gibt keine Alternative. Die Library funktioniert, ist aber explizit als "not feature complete" markiert.

**Architektur:**
- Nutzt `VoiceRecvClient` als drop-in für `VoiceClient`
- `AudioSink` als Gegenstück zu `AudioSource` — callback-basiert
- Speaker-Detection eingebaut (`get_speaking()`, Speaking-Events)
- Keine Monkey-Patches oder Hacks nötig

### Bekannte Issues (lange Sessions)

**Direkte Long-Session-Bugs:** Keine explizit gemeldeten Memory-Leak-Issues für die Library selbst. ABER:

1. **Decryption Errors** (Issue #38, April 2025): Gelegentliche Entschlüsselungsfehler beim Audio-Stream. Ursache unklar — könnte bei langen Sessions häufiger auftreten wenn Discord die Encryption rotiert.

2. **Discord selbst** hat Memory-Leak-Probleme bei langen Voice-Sessions (bekanntes Problem). Das betrifft den Client, nicht die Library — aber ist für 2-4h Sessions relevant.

3. **Buffer-Management:** Die Library speichert Audio in Sinks. Bei 2-4h Sessions mit mehreren Speakern muss man:
   - Periodisch Chunks flushen (nicht alles im RAM halten)
   - Einen File-basierten Sink verwenden (oder eigenen schreiben)
   - Per-Speaker Streams getrennt aufnehmen (`MultiAudioSink`)

### Empfehlung

**Nutzbar, aber mit Vorsicht.** Es gibt keine Alternative für Discord Voice Receive in Python. Für 2-4h Sessions:
- Custom Sink implementieren der periodisch auf Disk schreibt
- Error-Handling für Decryption-Errors einbauen (Reconnect-Logik)
- Regelmäßig testen ob Updates Breaking Changes bringen (Alpha!)
- **Risiko:** Maintainer ist eine Einzelperson. Wenn die aufhört, gibt's keinen Support.

**Risikobewertung: MITTEL** — funktioniert, ist aber fragil. Plan B sollte existieren (z.B. Bot-seitige Aufnahme via FFmpeg direkt vom Audio-Stream).

---

## 2. faster-whisper vs. openai-whisper

### Vergleich

| Aspekt | openai-whisper | faster-whisper |
|--------|---------------|----------------|
| **Engine** | PyTorch | CTranslate2 (quantisiert) |
| **Speed** | 1× (Baseline) | **4× schneller** bei gleicher Accuracy |
| **RAM** | Hoch (large-v3: ~10GB) | **~50% weniger** |
| **GPU** | CUDA erforderlich für Speed | CUDA + CPU-Fallback |
| **Modelle** | tiny → large-v3, turbo | Gleiche Modelle (konvertiert) |
| **initial_prompt** | ✅ Ja | ✅ Ja |
| **Language Detection** | ✅ | ✅ |
| **Word Timestamps** | ✅ (via --word_timestamps) | ✅ |
| **Maintenance** | OpenAI, selten Updates | SYSTRAN, aktiver |
| **Long-form Audio** | Halluzinationsprobleme bei large-v3 | Gleiche Engine, gleiche Probleme |

### DE/EN-Mix mit RPG-Eigennamen

**Das Kernproblem:** Whisper (beide Implementierungen) erwartet **eine Sprache pro Segment**. Bei DE/EN-Mix:
- Wenn `language="de"`: Englische Eigennamen werden als deutsches Kauderwelsch transkribiert
- Wenn `language="en"`: Deutsche Sätze werden ignoriert oder verfälscht
- Wenn `language=None` (auto-detect): Erkennt pro Segment, aber wechselt nicht mid-sentence

**Für RPG-Eigennamen (Fantasy-Namen):**

`initial_prompt` ist der Schlüssel. Beide Implementierungen unterstützen es:

```python
# faster-whisper Beispiel:
segments, info = model.transcribe(
    "session.wav",
    language="de",  # Primärsprache
    initial_prompt="Charaktere: Thalindra, Grimjaw, Kael'thas. Orte: Mondscheinwald, Eisenfeste. Begriffe: Naturzauber, Initiativwurf, W20."
)
```

Der `initial_prompt` biased das Sprachmodell Richtung dieser Begriffe — keine Garantie, aber deutliche Verbesserung. Funktioniert am besten wenn die Namen "plausibel klingen" (Thalindra → ja, Xq7bz → nein).

**Modellempfehlung:**
- **large-v3-turbo**: Bester Kompromiss Speed/Accuracy für Deutsch
- **large-v2**: Weniger Halluzinationen als v3 bei langen Aufnahmen!
- **large-v3**: Höchste theoretische Accuracy, aber bekannte Halluzinationsprobleme bei >30 Min Audio

⚠️ **Halluzinationen bei langen Sessions:** Whisper (alle Varianten) neigt bei langen Audio-Files zu:
- Wiederholungen (gleicher Satz 100× transkribiert)
- Phantom-Text bei Stille
- "Danke fürs Zuschauen" / "Subscribe" am Ende (YouTube-Trainingsdaten-Artefakt)

**Gegenmaßnahmen:**
1. Audio in 5-10 Min Chunks schneiden VOR der Transkription
2. VAD (Voice Activity Detection) vorschalten — `faster-whisper` hat `vad_filter=True` eingebaut
3. `condition_on_previous_text=False` setzen (verhindert Halluzinations-Kaskaden)
4. Nachverarbeitung: Wiederholungen erkennen und entfernen

### Empfehlung

**faster-whisper mit large-v3-turbo (oder large-v2 als Fallback).**

Gründe:
- 4× schneller = 2-4h Session in ~30-60 Min transkribiert statt 2-4h
- 50% weniger RAM = läuft auf Consumer-GPUs
- Gleiche Accuracy wie openai-whisper
- `initial_prompt` für RPG-Begriffe unterstützt
- `vad_filter=True` gegen Halluzinationen bei Stille
- Aktiver maintained als openai-whisper

**Risikobewertung: NIEDRIG** — faster-whisper ist production-ready und weit verbreitet.

---

## 3. Wavesurfer.js

### Übersicht

| Aspekt | Bewertung |
|--------|-----------|
| **Package** | wavesurfer.js (npm) |
| **Version** | v7+ (aktuelle Major) |
| **GitHub** | katspaugh/wavesurfer.js |
| **Stars** | ~9.000+ |
| **Lizenz** | BSD-3-Clause |
| **Plugins** | Regions, Timeline, Minimap, Spectrogram, u.a. |

### Long-Audio Performance (2-4h)

**⚠️ Das ist DAS Problem mit Wavesurfer.js:**

> "Since wavesurfer decodes audio entirely in the browser using Web Audio, large clips may fail to decode due to memory constraints." — Offizielle Docs

**Was passiert bei 2-4h Audio:**
- Browser muss das gesamte Audio dekodieren → **GB-weise RAM**
- Web Audio API hat Größenlimits (je nach Browser: 2GB oder weniger)
- Waveform-Rendering für Millionen von Samples → UI-Freeze

**Lösung: Pre-decoded Peaks**

Wavesurfer unterstützt vorberechnete Peak-Daten. Statt das Audio im Browser zu dekodieren:

```javascript
const wavesurfer = WaveSurfer.create({
  container: '#waveform',
  // Audio URL for playback
  url: '/api/session/123/audio.opus',
  // Pre-computed peaks (server-side generiert)
  peaks: [peakData],  // Float32Array mit ~8000 Samples pro Stunde
  duration: 14400,     // 4h in Sekunden
})
```

**Peaks server-side generieren:**
```bash
# Via audiowaveform (BBC Tool):
audiowaveform -i session.wav -o peaks.json --pixels-per-second 2
# Oder via ffmpeg:
ffmpeg -i session.wav -filter_complex "compand,aformat=sample_fmts=s16" -f wav - | audiowaveform --input-format wav -o peaks.json
```

Mit Pre-decoded Peaks funktioniert Wavesurfer auch für 4h+ Audio, weil:
- Kein Browser-Decoding nötig
- Peak-File ist nur ein paar KB groß
- Audio wird per MediaElement gestreamt (nicht komplett geladen)

### Regions Plugin für Speaker-Segmente

**Ja, das ist genau der Use-Case.** Das Regions Plugin kann:

```javascript
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.js'

const regions = wavesurfer.registerPlugin(RegionsPlugin.create())

// Speaker-Segmente aus Transkription laden:
transcription.segments.forEach(seg => {
  regions.addRegion({
    start: seg.start,
    end: seg.end,
    content: `${seg.speaker}: ${seg.text}`,
    color: speakerColors[seg.speaker],  // Farbe pro Sprecher
    drag: false,
    resize: false,
  })
})

// Click-to-play für Regionen:
regions.on('region-clicked', (region, e) => {
  e.stopPropagation()
  region.play()
})
```

**Features die für RPG-Recorder relevant sind:**
- Farbcodierung pro Sprecher ✅
- Click-to-play Regionen ✅
- Drag & Resize (für manuelle Korrekturen) ✅
- Overlap-Darstellung (mehrere Sprecher gleichzeitig) ✅
- Content-Labels in Regionen ✅
- Automatische Regions aus Silence-Detection ✅

### Empfehlung

**Wavesurfer.js ist die richtige Wahl — aber NUR mit Pre-decoded Peaks.**

Ohne Peaks: unbrauchbar für 2-4h Audio.
Mit Peaks: funktioniert hervorragend.

**Pipeline:**
1. Audio aufnehmen (discord-ext-voice-recv)
2. Peaks server-side generieren (`audiowaveform`)
3. Transkribieren (faster-whisper)
4. Speaker Diarization (optional: `pyannote.audio`)
5. Frontend: Wavesurfer.js mit Peaks + Regions Plugin

**Risikobewertung: NIEDRIG** — mature Library, aktiv maintained, großes Ökosystem.

---

## Gesamtempfehlung Tech Stack

| Komponente | Empfehlung | Risiko |
|------------|-----------|--------|
| Voice Receive | discord-ext-voice-recv | ⚠️ MITTEL (Alpha, Single Maintainer) |
| Transkription | faster-whisper + large-v3-turbo | ✅ NIEDRIG |
| Custom Vocabulary | `initial_prompt` mit RPG-Begriffen | ✅ NIEDRIG |
| Waveform UI | Wavesurfer.js + Pre-decoded Peaks | ✅ NIEDRIG |
| Speaker-Segmente | Regions Plugin | ✅ NIEDRIG |
| Speaker Diarization | pyannote.audio (optional, P2) | ⚠️ MITTEL (GPU, Komplexität) |

**Haupt-Risiko:** discord-ext-voice-recv ist Alpha mit einem einzelnen Maintainer. Falls das bricht, braucht ihr einen Plan B (z.B. direktes FFmpeg-Recording vom Discord Audio-Stream, oder Self-Bot-Ansatz).

---

*Research: Nova 🔭 | Stand: März 2026*
