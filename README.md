# Spielezentrum

Dieses Projekt enthält eine Desktop-Anwendung mit Login, Spielauswahl und mehreren Spielmodi.

## Dateien

- `spielezentrum.py` — Hauptanwendung
- `build.ps1` — PowerShell-Build-Skript
- `build.bat` — Windows-Build-Skript
- `version.txt` — Versionsnummer für Builds
- `release/` — Ausgabeort für gebaute Exe-Dateien
- `CHANGELOG.md` — Änderungsverlauf

## Build und Veröffentlichung

### Voraussetzungen

- Python installiert
- `customtkinter` installiert
- `pyinstaller` installiert

### Erster Build

```powershell
python -m pip install customtkinter pyinstaller
.\build.ps1
```

oder unter der Eingabeaufforderung:

```bat
build.bat
```

### Ergebnis

- Die ausführbare Datei wird in `dist\` erstellt
- Eine Version mit Namen `spielezentrum_x.y.z.exe` wird nach `release\` kopiert
- Eine ZIP-Datei `spielezentrum_vx.y.z.zip` wird ebenfalls in `release\` abgelegt

## Automatisches Release mit GitHub Actions

Du kannst automatische Builds und Releases erstellen, wenn du ein Tag wie `v1.0.0` pusht.
Eine Beispiel-Workflow-Datei ist unter `.github/workflows/release.yml` enthalten. Sie:

- setzt die Datei `version.txt` aus dem Tag (entfernt führendes `v`)
- führt `build.bat` aus
- erstellt ein GitHub Release und lädt die ZIP-Datei aus `release/` hoch

Vor dem Nutzen:

- Passe `update_config.json` oder `update_config_example.json` an dein GitHub-Repository an (ersetze `<owner>` und `<repo>`).
- Stelle sicher, dass `requirements.txt` und `build.bat` im Repository existieren.

Wenn du Hilfe brauchst, passe ich `update_config.json` automatisch auf dein Repository an.

## Versionsverwaltung

- Ändere `version.txt` bei jedem Release
- Aktualisiere `CHANGELOG.md` mit den neuen Änderungen

## Updates veröffentlichen

1. Ändere oder erweitere `spielezentrum.py`
2. Erhöhe die Versionsnummer in `version.txt`
3. Aktualisiere `CHANGELOG.md`
4. Führe `build.ps1` oder `build.bat` aus
5. Lade die neue `release\spielezentrum_vx.y.z.zip` hoch

## Nutzung der veröffentlichten Version

- Nutzer laden die ZIP-Datei herunter
- Entpacken optional `spielezentrum.exe`
- Starten die Anwendung per Doppelklick

## Code-Signing (optional)

Du kannst die erzeugten Exe-Dateien in der CI automatisch mit einem PFX-Zertifikat signieren. Der Workflow unterstützt das, wenn zwei GitHub-Secrets gesetzt sind:

- `CODE_SIGN_PFX`: Inhalt der `.pfx`-Datei, base64-codiert (als Secret)
- `CODE_SIGN_PASSWORD`: Passwort zum PFX

Hinweis:
- Die Signatur-Schritte laufen nur auf `windows-latest` und prüfen auf das Vorhandensein der Secrets.
- Der Runner verwendet `signtool.exe` (Windows SDK). Falls `signtool` nicht verfügbar ist, kannst du stattdessen `osslsigncode` oder einen dedizierten Signing-Action nutzen.
- Für breitere Vertrauenswürdigkeit (keine SmartScreen-Warnungen) ist ein EV-Code-Signing-Zertifikat empfehlenswert.

Vorgehen zum Setzen der Secrets:

1. Exportiere dein PFX lokal und konvertiere in Base64:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes('C:\pfad\zu\cert.pfx')) | Out-File -Encoding ascii pfx.b64
```

2. Kopiere den Inhalt von `pfx.b64` und lege ein neues Repository-Secret `CODE_SIGN_PFX` an. Setze `CODE_SIGN_PASSWORD` auf das PFX-Passwort.

3. Erstelle ein Release-Tag wie gewohnt; CI signiert dann die Artefakte, falls die Secrets vorhanden sind.
