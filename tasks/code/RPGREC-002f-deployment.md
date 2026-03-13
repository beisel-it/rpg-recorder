# Task: systemd Service + Deployment
Shortcode: RPGREC-002f
Epic: RPGREC-002
Stage: code
Status: ready for code
Priority: P1
Assigned: Wilbur
Depends: RPGREC-002e
Estimated: 1h

## Definition of Done
- [ ] systemd user-service Unit-File (`rpg-recorder.service`)
- [ ] `Restart=on-failure`, `RestartSec=5`
- [ ] `ExecStart` mit korrektem Python-Path + venv
- [ ] Output-Dir + Log-Dir als Environment in Unit-File
- [ ] Deploy-Script: `scripts/deploy.sh` (git pull, pip install, systemctl restart)
- [ ] Läuft auf beisel.it, Bot ist online nach `systemctl start`

## Acceptance Criteria
1. `systemctl --user start rpg-recorder` → Bot online in <10s
2. `kill -9 $(pidof python)` → Service restarted automatisch
3. `journalctl --user -u rpg-recorder` → Logs sichtbar + sauber formatiert

## Comments
- Branch: `feature/RPGREC-002f-deploy`
