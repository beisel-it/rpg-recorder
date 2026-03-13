# Task: Reconnect-Watchdog + Health-Monitoring
Shortcode: RPGREC-002e
Epic: RPGREC-002
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur
Depends: RPGREC-002d
Estimated: 2h

## Definition of Done
- [ ] Background-Task prüft alle 5s ob Voice-Connection noch steht
- [ ] Bei Disconnect: automatischer Rejoin + Sink-Restart innerhalb 10s
- [ ] Lücke im Audio wird mit Stille gefüllt (kein Zeitversatz nach Reconnect)
- [ ] Health-Log: Bytes/Minute pro Speaker, alle 60s geloggt
- [ ] Warning wenn ein Speaker >60s kein Audio liefert (aber noch connected)
- [ ] Discord-Nachricht bei Reconnect: „⚠️ Verbindung kurz unterbrochen — Aufnahme läuft weiter"

## Acceptance Criteria
1. Netzwerk-Unterbrechung simulieren (iptables drop 5s) → Bot reconnected, Audio geht weiter
2. Health-Log zeigt Bytes/Min pro Speaker → Werte plausibel (>0 wenn jemand spricht)
3. Speaker muted seit 2 Min → Warning im Log (kein Crash, nur Info)

## Comments
- Branch: `feature/RPGREC-002e-watchdog`
