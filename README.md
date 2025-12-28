# VideoPlayer

**VideoPlayer** ist eine kompakte Flask-Web-App zum Abspielen **lokaler Video-Dateien** direkt im Browser. Sie ist auf typische Serien-/Anime-Ordnerstrukturen ausgelegt (Staffeln/Episoden) und kann unkompliziert **via Docker** oder lokal betrieben werden.

> ⚠️ **Work in progress:** Die App ist nutzbar, aber UI/Features sind noch im Ausbau und können sich ändern.
> Feedback, Issues und Pull Requests sind sehr willkommen – **help is appreciated** 🙌

---

## Features (aktuell)

- 📚 **Bibliothek/Browse**: Medien unter `media/` browsen (inkl. Pagination)
- 🎬 **Watch-Seite**: Wiedergabe im Browser (Frontend via Video.js)
- 🧩 **Modularer Aufbau**: Blueprints, Utils und Config getrennt
- 💾 **Persistenz ohne Datenbank**: z.B. Cache für Mediengrößen (`instance/media_size_cache.json`)
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

2. `.env` anlegen (mindestens `SECRET_KEY` setzen)

```bash
touch .env
```

3. Container bauen & starten

```bash
docker compose up --build
```

4. Im Browser öffnen

- http://localhost:8000

**Medien hinzufügen:** Lege deine Dateien/Ordner unter `media/` ab (wird im Docker-Setup in den Container gemountet).

---

## Installation (lokal, ohne Docker)

**Voraussetzungen:** Python (empfohlen: 3.11+), `pip`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Lege anschließend eine `.env` an und setze mindestens `SECRET_KEY` (siehe Konfiguration).

Start (Dev):

```bash
python run.py
```

Alternativ „prod-nah“ (wie im Container typischerweise):

```bash
gunicorn -b 0.0.0.0:8000 wsgi:app
```

---

## Konfiguration

Die App nutzt Umgebungsvariablen (optional aus einer `.env`). Welche Werte verfügbar sind, ist in `videoplayer/config.py` definiert.

**Wichtige Variablen (Auswahl):**

- `SECRET_KEY` (**Pflicht**) – Session/CSRF-Schutz
- `MEDIA_ROOT` – Pfad zur Medienbibliothek (Standard: `media/` im Projekt)
- `HOST` / `PORT` – Bind-Adresse und Port (Docker nutzt i.d.R. `:8000`)
- `DEBUG` – Debug-Modus (nur lokal)
- `DEFAULT_PER_PAGE` – Pagination-Größe in der Browse-Ansicht
- `RATE_LIMIT_ENABLED` – aktivieren/deaktivieren von Rate Limiting

Tipp: Wenn du die App im Heimnetz erreichbar machen willst, setze `HOST=0.0.0.0` und beachte die Security-Hinweise unten.

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

- 🔒 **Fürs Heimnetz gedacht:** Es gibt aktuell **keine Benutzerverwaltung/Authentifizierung**. Bitte nicht unverändert öffentlich ins Internet exponieren.
- 🧷 **`SECRET_KEY` setzen:** erforderlich für sichere Sessions/CSRF.
- 🧭 **Pfadvalidierung:** Routen sollten nur innerhalb von `MEDIA_ROOT` auf echte Dateien zugreifen (Schutz vor Directory Traversal).
- ⏱️ **Rate Limiting:** kann (je nach Konfiguration) aktiv sein und hilft gegen Missbrauch.

Wenn du die App öffentlich betreiben willst, sind vorgeschaltet z.B. Authentifizierung (Reverse Proxy), HTTPS und ein restriktives Netz-/Firewall-Setup empfehlenswert.

---

## Roadmap (Auswahl)

- 🔎 Suche über Titel/Dateinamen
- ⚙️ Erweiterte Einstellungen
- 🗄️ Persistente Speicherung via Datenbank
- 👤 Benutzerverwaltung / Authentifizierung
- 🧪 Mehr Tests und CI/CD

---

## Contributing

Beiträge sind willkommen 😊

- **Bugs/Ideen:** bitte als GitHub Issue mit Repro-Schritten
- **Pull Requests:** gerne klein und fokussiert (mit kurzer Beschreibung)
- **Tests:** falls möglich, passende Tests ergänzen/aktualisieren

---

## Rechtlicher Hinweis

Bitte verwende nur Medien, an denen du die nötigen Rechte hast. Dieses Projekt stellt lediglich eine lokale Abspieloberfläche bereit.
