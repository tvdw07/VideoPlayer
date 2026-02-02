# VideoPlayer

**VideoPlayer** ist eine schlanke Flask-Web-App zum Abspielen **lokaler Video-Dateien** direkt im Browser. Sie richtet sich an typische Serien-/Anime-Ordnerstrukturen (Staffeln/Episoden) und wird **via Docker mit PostgreSQL** betrieben.

> ⚠️ **Work in progress:** Die App ist nutzbar, aber UI/Features sind noch im Ausbau und können sich ändern.
> Feedback, Issues und Pull Requests sind sehr willkommen.

---

## Features (aktuell)

- 📚 **Bibliothek/Browse**: Medien unter `media/` durchsuchen (inkl. Pagination)
- 🔎 **Suche**: Titel- und Dateinamen-Suche
- 🎬 **Watch-Seite**: Wiedergabe im Browser (Frontend via Video.js)
- 👤 **Authentifizierung**: Login-geschützte Nutzung
- 🗄️ **Datenbank**: Persistenz für App-Daten
- 🧩 **Modularer Aufbau**: Blueprints, Utils und Config getrennt
- 🐳 **Docker-ready**: schneller Start über `docker compose`

**Hinweis:** Es findet **kein Transcoding** statt („Direct Play“). Ob ein Video abspielbar ist, hängt von den Codecs deines Browsers ab.

---

## Quickstart (Docker Compose)

**Voraussetzungen:** Docker + Docker Compose

1. Repository klonen

```bash
git clone https://github.com/tvdw07/VideoPlayer.git
cd VideoPlayer
```

2. `.env` anlegen und konfigurieren

```bash
touch .env
```

Setze mindestens folgende Variablen (oder nutze die Defaults):

```env
SECRET_KEY=your-secret-key-here
POSTGRES_USER=videoplayer
POSTGRES_PASSWORD=change-me
POSTGRES_DB=videoplayer
PORT=8000
```

3. Container bauen & starten

```bash
docker compose up --build
```

4. Im Browser öffnen

- http://localhost:8000

**Medien hinzufügen:** Lege deine Dateien/Ordner unter `media/` ab (wird im Docker-Setup in den Container gemountet).

---

## Systemanforderungen

Die App wird ausschließlich via Docker mit PostgreSQL betrieben. Folgende Komponenten werden benötigt:

- **Docker** (Version 20.10+)
- **Docker Compose** (Version 1.29+)
- Mindestens **512 MB freier RAM** (empfohlen: 1 GB+)
- PostgreSQL wird im Container automatisch bereitgestellt

---

## Konfiguration

Die App nutzt Umgebungsvariablen aus einer `.env`-Datei. Die verfügbaren Optionen sind in `videoplayer/config.py` dokumentiert.

**Erforderliche Variablen:**

- `SECRET_KEY` – Session/CSRF-Schutz
- `POSTGRES_DB` – PostgreSQL Datenbank-Name (Standard: `videoplayer`)
- `POSTGRES_USER` – PostgreSQL Benutzername (Standard: `videoplayer`)
- `POSTGRES_PASSWORD` – PostgreSQL Passwort (Standard: `change-me`)

**Optionale Variablen:**

- `PORT` – Port der App (Standard: `8000`)
- `HOST` – Bind-Adresse (Standard: `0.0.0.0`)
- `MEDIA_ROOT` – Pfad zur Medienbibliothek (Standard: `media/`)
- `DEFAULT_PER_PAGE` – Pagination-Größe (Standard: `12`)
- `RATE_LIMIT_ENABLED` – Rate Limiting aktivieren (Standard: `true`)
- `REDIS_URL` – Redis-Verbindung für den Limiter (z.B. `redis://redis:6379/0`)

---

## Medien-Struktur

Die App erwartet Medien unterhalb von `MEDIA_ROOT` (standardmäßig `media/`). Typische Struktur:

- `media/anime/<Titel>/…S01E001….mp4`
- `media/series/<Titel>/Season 01/…`
- `media/movies/<Titel>.mp4`

Die Erkennung ist auf Serien-/Episodenmuster ausgelegt (z.B. `S01E001`).

---

## Projektstruktur (kurz)

- `videoplayer/` – App-Code (App-Factory, Config, Utils)
- `videoplayer/routes/` – Blueprints/Routes (`browse`, `watch`, `media`, `settings`)
- `templates/` – Jinja2 Templates
- `static/` – CSS/JS (u.a. `static/js/player.js`)
- `media/` – lokale Medienbibliothek (wird nicht versioniert gedacht)
- `instance/` – Laufzeitdaten (z.B. Cache-Dateien)
- `tests/` – Tests (z.B. Pagination/Security/Cache)

---

## Security / Betriebshinweise

- 🔒 **Fürs Heimnetz gedacht:** Es gibt Authentifizierung, aber bitte nicht unverändert öffentlich ins Internet exponieren.
- 🧷 **`SECRET_KEY` setzen:** erforderlich für sichere Sessions/CSRF.
- 🧭 **Pfadvalidierung:** Routen sollten nur innerhalb von `MEDIA_ROOT` auf echte Dateien zugreifen (Schutz vor Directory Traversal).
- ⏱️ **Rate Limiting:** Der Limiter arbeitet mit Redis und hilft gegen Missbrauch.

Wenn du die App öffentlich betreiben willst, sind vorgeschaltet z.B. HTTPS, ein restriktives Netz-/Firewall-Setup und ggf. zusätzlicher Reverse-Proxy-Schutz empfehlenswert.

---

## Roadmap (Auswahl)

- ⏯️ Wiedergabefortschritt in der DB speichern (wie weit wurde geschaut)
- 🛡️ Erweiterte Brute-Force-Protection mit DB-Unterstuetzung
- 🧑‍💼 Admin-Dashboard fuer mehrere Nutzer
- 🧾 Erweitertes Logging
- 🧠 Bessere Lesbarkeit durch mehr Kommentare
- 🧪 Mehr Tests
- ⚙️ Erweiterte Einstellungen
- 🎨 Design-Update (optional)
- ⬆️ Optional: Uploads auf den Server erlauben

---

## Contributing

Beiträge sind willkommen 😊

- **Bugs/Ideen:** bitte als GitHub Issue mit Repro-Schritten
- **Pull Requests:** gerne klein und fokussiert (mit kurzer Beschreibung)
- **Tests:** falls möglich, passende Tests ergänzen/aktualisieren

---

## Rechtlicher Hinweis

Bitte verwende nur Medien, an denen du die nötigen Rechte hast. Dieses Projekt stellt lediglich eine lokale Abspieloberfläche bereit.
