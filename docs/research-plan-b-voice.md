# Plan B: Voice Receive Alternativen — RPG Recorder

**RPGREC-005** | Researcher: Nova 🔭 | Datum: 2026-03-13

---

## 🚨 BREAKING: Discord DAVE/E2EE Enforcement (seit 2. März 2026)

**Bevor wir über Plan B reden: Plan A hat ein neues, kritisches Problem.**

Seit dem **2. März 2026** erzwingt Discord das DAVE-Protokoll (Audio & Video End-to-End Encryption) für **alle** Voice-Verbindungen. Bots ohne DAVE-Support bekommen Error 4017 und können nicht mehr joinen.

**Konsequenzen für alle Kandidaten:**

| Library | DAVE-Support? | Status |
|---------|--------------|--------|
| **discord.py** (Rapptz) | ✅ **Ja** — PR #10300 merged (via `davey` Dep) | Funktioniert |
| **discord-ext-voice-recv** | ⚠️ Hängt von discord.py ab — braucht aktuelle Version | Sollte funktionieren wenn discord.py DAVE hat |
| **disnake** | ✅ **Ja** — via `dave.py` Bindings (Changelog) | Funktioniert |
| **pycord** | ❌ **Nein** — Issue #3135 offen, Error 4017 | **KAPUTT seit 2. März 2026** |
| **discord.js** (@discordjs/voice) | ⚠️ Bugs — Issue #11419 (Reconnect-Loops, kein Audio) | Instabil |

**Das verändert die Bewertung fundamental.** Pycord — das einzige Framework mit nativem `start_recording()` — ist aktuell nicht nutzbar für Voice.

---

## Kandidaten-Evaluation

### 1. Pycord (`py-cord`)

| Aspekt | Bewertung |
|--------|-----------|
| **Voice Receive** | ✅ Nativ: `start_recording()` mit Sink-System |
| **Multi-User** | ✅ Per-User Audio-Streams, `sync_start` für Synchronisation |
| **DAVE-Support** | ❌ **Fehlt** — Error 4017, Voice komplett kaputt |
| **Bekannte Bugs** | Issue #1432: Voice Receive stoppt nach kurzer Zeit; Issue #2921: Opus Decode Errors (intermittent); Issue #3135: DAVE/E2EE nicht implementiert |
| **Maintenance** | Aktiv, aber DAVE-Support fehlt noch |
| **Aufwand** | ~0.5 Tage (wenn DAVE gefixt) — API ist am einfachsten |

**Urteil: AUSGESCHLOSSEN bis DAVE-Support kommt.** Selbst danach: Issue #1432 (Voice Receive stoppt) ist ein Showstopper für 2-4h Sessions und wurde nie gefixt.

---

### 2. Disnake

| Aspekt | Bewertung |
|--------|-----------|
| **Voice Receive** | ❌ **Kein nativer Voice Receive** — nur Voice Send |
| **DAVE-Support** | ✅ Implementiert via `dave.py` (DisnakeDev/dave.py) |
| **Multi-User** | N/A — kein Receive |
| **Maintenance** | Aktiv, professionelles Team |
| **Aufwand** | ⚠️ Hoch — müsste Voice Receive selbst implementieren |

**Urteil: DAVE funktioniert, aber kein Voice Receive.** Man müsste entweder `discord-ext-voice-recv` portieren oder den Raw-UDP-Stream manuell dekodieren. Aufwand: 3-5 Tage für einen erfahrenen Dev. Nicht empfohlen als Plan B.

---

### 3. discord.py + discord-ext-voice-recv (aktualisierte Bewertung)

| Aspekt | Bewertung |
|--------|-----------|
| **Voice Receive** | ✅ Via discord-ext-voice-recv |
| **DAVE-Support** | ✅ discord.py PR #10300 merged (via `davey`) |
| **Multi-User** | ✅ Per-Speaker Streams via `MultiAudioSink` |
| **Maintenance** | discord.py: aktiv. ext-voice-recv: Single Maintainer, Alpha |
| **Long Sessions** | ⚠️ Keine expliziten Bugs bekannt, aber Alpha-Disclaimer |
| **Aufwand** | ~1 Tag für Custom Disk-Sink + Error-Handling |

**Urteil: AKTUELL DIE EINZIGE FUNKTIONIERENDE OPTION.** discord.py hat DAVE, ext-voice-recv baut darauf auf. Die Combo funktioniert — ist aber fragil (Alpha, Single Maintainer).

---

### 4. discord.js + @discordjs/voice (JavaScript/Node.js)

| Aspekt | Bewertung |
|--------|-----------|
| **Voice Receive** | ✅ `VoiceConnection.receiver` mit `subscribe()` pro User |
| **DAVE-Support** | ⚠️ v0.19.x hat DAVE — aber Issue #11419: Reconnect-Loops + kein Audio |
| **Multi-User** | ✅ Per-User Opus Streams |
| **Maintenance** | Sehr aktiv (offizielles Discord-Team) |
| **Sprachwechsel** | ❌ Projekt ist Python-basiert — Node.js wäre Fremdkörper |
| **Aufwand** | ~2 Tage + Architekturfrage (Microservice oder alles umschreiben?) |

**Urteil: Technisch möglich, aber DAVE-Bugs aktuell + Sprachwechsel.** Falls Python-Ökosystem scheitert, wäre ein Node.js-Microservice für Voice-Recording eine Option. Aber: Die DAVE-Bugs in discord.js zeigen, dass auch hier noch nicht alles stabil ist.

---

### 5. Mumble + mumblerecbot (Alternative Plattform)

| Aspekt | Bewertung |
|--------|-----------|
| **Voice Receive** | ✅ Server-seitig oder via pymumble Client-Bot |
| **DAVE** | N/A — Mumble hat eigene Verschlüsselung |
| **Multi-User** | ✅ Per-User Streams (pymumble) |
| **Long Sessions** | ✅ Mumble ist für lange Sessions ausgelegt |
| **Maintenance** | pymumble: Low-Activity. mumblerecbot: letzter Commit >2 Jahre |
| **Aufwand** | ~2 Tage Implementierung, ABER: User müssen Mumble nutzen statt Discord |

**Urteil: Technisch solide, aber UX-Dealbreaker.** RPG-Gruppen sind auf Discord. Einen Plattformwechsel zu erzwingen ist unrealistisch. Als Nischen-Option für technikaffine Gruppen ok, für ein Produkt nicht.

---

### 6. Custom WebSocket (Raw Discord Voice Gateway)

| Aspekt | Bewertung |
|--------|-----------|
| **Voice Receive** | ✅ Theoretisch — UDP Opus-Streams direkt empfangen |
| **DAVE-Support** | ❌ Müsste libdave manuell integrieren |
| **Multi-User** | ✅ SSRC-basierte Demultiplexing |
| **Aufwand** | 🔴 **Extrem hoch** — 2-4 Wochen, Voice Gateway + DAVE + Opus + Jitter Buffer |

**Urteil: NUR als allerletzter Ausweg.** Der Aufwand steht in keinem Verhältnis zum Nutzen, solange discord.py + ext-voice-recv funktioniert.

---

## Vergleichsmatrix

| Kriterium | discord.py + ext-recv | Pycord | Disnake | discord.js | Mumble | Custom WS |
|-----------|----------------------|--------|---------|------------|--------|-----------|
| **Voice Receive** | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| **DAVE/E2EE** | ✅ | ❌ | ✅ | ⚠️ | N/A | ❌ |
| **Multi-User ≥2** | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| **2-4h Stabilität** | ⚠️ | ❌ | — | ⚠️ | ✅ | ✅ |
| **Reconnect** | ⚠️ | ❌ | — | ⚠️ | ✅ | ✅ |
| **Aufwand** | 1 Tag | 0.5 Tag | 3-5 Tage | 2 Tage | 2 Tage | 2-4 Wochen |
| **Produktionsreif** | ⚠️ | ❌ | ❌ | ⚠️ | ✅ | ❌ |

---

## Empfehlung

### Plan A bleibt Plan A — aber mit Absicherung

**discord.py (mit DAVE) + discord-ext-voice-recv** ist aktuell die **einzige funktionierende Option** für Discord Voice Receive in Python. Es gibt keinen besseren Plan B innerhalb von Discord.

### Absicherungsstrategie (statt "Plan B")

Statt auf eine alternative Library zu hoffen, die es aktuell nicht gibt:

**1. Custom Disk-Sink mit Chunking (Prio 1, Tag 1)**
```python
class ChunkedFileSink(AudioSink):
    """Schreibt Audio in 5-Min WAV-Chunks auf Disk.
    Verhindert Memory-Leaks bei 2-4h Sessions."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.chunk_duration = 300  # 5 Min
        self.writers: dict[int, WavWriter] = {}
    
    def write(self, user, data):
        writer = self._get_or_rotate_writer(user)
        writer.write(data.pcm)
```

**2. Reconnect-Watchdog (Prio 1, Tag 1)**
```python
async def voice_watchdog(vc: VoiceRecvClient, channel):
    """Reconnect bei Verbindungsabbruch."""
    while recording:
        if not vc.is_connected():
            log.warning("Voice connection lost — reconnecting...")
            vc = await channel.connect(cls=VoiceRecvClient)
            vc.listen(sink)
        await asyncio.sleep(5)
```

**3. Health-Monitoring (Prio 2)**
- Bytes-pro-Minute pro Speaker tracken
- Alert wenn ein Speaker >60s kein Audio liefert
- Memory-Usage loggen

**4. Fallback-Aufnahme via lokalen Client (Nuclear Option)**
Falls die Bot-basierte Aufnahme komplett versagt:
- OBS/Craig Bot als manueller Fallback (User startet Recording)
- Audio-Import-Feature in der App, damit manuell aufgenommene Sessions trotzdem transkribiert werden können

### Strategische Empfehlung an Wilbur

> **Baue Plan A robust (Custom Sink + Watchdog + Monitoring), statt auf Plan B zu hoffen.**
> 
> Es gibt keinen ausgereiften Plan B. Pycord ist kaputt (DAVE), Disnake hat kein Voice Receive, discord.js hat DAVE-Bugs, Custom WebSocket ist Wochen an Arbeit. 
>
> Die beste Absicherung ist: discord.py + ext-voice-recv **defensiv implementieren** mit Chunking, Reconnect, und einem manuellen Import-Fallback.

---

## DAVE-Situation beobachten

Die DAVE-Enforcement ist 11 Tage alt. Die Lage ändert sich schnell:
- **Pycord** könnte DAVE nachliefern → dann wäre es eine echte Alternative
- **discord.js** DAVE-Bugs könnten gefixt werden → dann Node.js-Microservice als Option
- **ext-voice-recv** könnte Update brauchen für DAVE-Kompatibilität → Testen!

**Empfehlung:** Einmal pro Woche diese Issues checken:
- `Pycord-Development/pycord#3135` (DAVE)
- `discordjs/discord.js#11419` (DAVE Audio-Bugs)
- `imayhaveborkedit/discord-ext-voice-recv` (neue Releases)

---

*Research: Nova 🔭 | Stand: 13. März 2026*
