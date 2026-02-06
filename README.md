# VideoPlayer

**VideoPlayer** ist eine schlanke Flask-Web-App zum Abspielen **lokaler Video-Dateien** direkt im Browser. Sie richtet sich an typische Serien-/Anime-Ordnerstrukturen (Staffeln/Episoden) und wird **via Docker Compose mit PostgreSQL, Redis und Nginx (Reverse Proxy)** betrieben.

> ⚠️ **Work in progress:** Die App ist nutzbar, aber UI/Features sind noch im Ausbau und können sich ändern.
> Feedback, Issues und Pull Requests sind sehr willkommen.

---

## Features (aktuell)

- 📚 **Bibliothek/Browse**: Medien unter `media/` durchsuchen (inkl. Pagination)
- 🔎 **Suche**: Titel- und Dateinamen-Suche
- 🎬 **Watch-Seite**: Wiedergabe im Browser (Frontend via Video.js)
- 👤 **Authentifizierung**: Login-geschützte Nutzung
- 🛡️ **Brute-Force-Protection**: Account-Lockout nach zu vielen Login-Versuchen (DB-Felder)
- 🗄️ **Datenbank**: Persistenz für App-Daten
- ⏱️ **Rate Limiting**: via Flask-Limiter + Redis-Backend
- 🧩 **Modularer Aufbau**: Blueprints, Utils und Config getrennt
- 🐳 **Docker-ready**: Start über Compose (Basis + lokale/Prod Overrides)
- 🔐 **HTTPS (auch lokal)**: via Nginx Reverse Proxy

**Hinweis:** Es findet **kein Transcoding** statt („Direct Play“). Ob ein Video abspielbar ist, hängt von den Codecs deines Browsers ab.

---

## Quickstart (Docker Compose, lokal via HTTPS)

**Voraussetzungen:** Docker + Docker Compose

### 1) Repository klonen

```bash
git clone https://github.com/tvdw07/VideoPlayer.git
cd VideoPlayer
```

### 2) `.env` anlegen

Am einfachsten kopierst du die Beispieldatei:

```bash
cp .env.example .env
```

Passe mindestens `SECRET_KEY` und die Datenbank-Credentials an.

> Konfiguration erfolgt über die Compose-Dateien und `.env`. Genauere Dokumentation folgt; in `.env.example` sind die Variablen bereits recht ausführlich kommentiert.

### 3) Lokale TLS-Zertifikate erstellen

Für den lokalen Nginx-Proxy erwartet das Setup Zertifikate unter:

- `certs/local/fullchain.pem`
- `certs/local/privkey.key`

Erstelle den Ordner:

```bash
mkdir -p certs/local
```

Dann kannst du dir ein selbstsigniertes Zertifikat generieren (OpenSSL):

```bash
# im Projekt-Root ausführen
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout certs/local/privkey.key \
  -out certs/local/fullchain.pem \
  -subj "/CN=localhost"
```

**Wichtig:** Dein Browser wird dem Zertifikat nicht automatisch vertrauen. Für „grünes Schloss“ brauchst du eine lokale CA (z.B. `mkcert`) oder du importierst das Zertifikat manuell.

### 4) Container bauen & starten (Recreate)

Wenn du wirklich „sauber neu“ starten willst (inkl. Entfernen der Volumes/DB-Daten), nutze diesen Flow:

```bash
docker compose down -v
docker compose -f compose.yml -f compose.local.yml up -d --build
```

> Hinweis: `down -v` löscht **Volumes** (z.B. Postgres-Daten). Verwende das nur, wenn du das wirklich möchtest.

### 5) Admin-User anlegen

Lege danach (einmalig) einen Admin-User an:

```bash
docker compose exec videoplayer flask create-user admin --admin
```

### 6) Container neu starten

Damit alles sauber neu lädt:

```bash
docker compose restart
```

### 7) Im Browser öffnen

- https://localhost/

(HTTP auf Port 80 wird auf HTTPS umgeleitet.)

**Medien hinzufügen:** Lege deine Dateien/Ordner unter `media/` ab (wird in den Container gemountet).

---

## Production (Hinweis)

Für eine produktive Umgebung gibt es ein separates Override:

```bash
docker compose -f compose.yml -f compose.prod.yml up -d --build
```

Das Prod-Setup erwartet Zertifikate unter:

- `certs/prod/fullchain.pem`
- `certs/prod/privkey.key`
---

## Systemanforderungen

Die App wird via Docker betrieben. Folgende Komponenten werden benötigt:

- **Docker** (Version 20.10+)
- **Docker Compose**
- Mindestens **512 MB freier RAM** (empfohlen: 1 GB+)

---

## Konfiguration

- Zentrale Umgebungsvariablen: `.env` (Vorlage: `.env.example`)
- Compose-Files:
  - `compose.yml` (Basis: App + Postgres + Redis)
  - `compose.local.yml` (lokal: Nginx + Mounts für `nginx/local.conf` und `certs/local`)
  - `compose.prod.yml` (prod: Nginx + Mounts für `nginx/prod.conf` und `certs/prod`)

**Wichtige Variablen (Auszug):**

- `SECRET_KEY` – Session/CSRF-Schutz (**required**)
- `DATABASE_URL` – SQLAlchemy-URI (zeigt im Docker-Setup auf Service `postgres`)
- `RATELIMIT_STORAGE_URI` – Redis-URI (im Docker-Setup i.d.R. `redis://redis:6379/0`)
- `AUTH_ENABLED` – Auth Master-Switch (**muss** in Prod `TRUE` sein; App verweigert sonst den Start)
- Cookie Settings für HTTPS:
  - `SESSION_COOKIE_SECURE=TRUE`
  - `REMEMBER_COOKIE_SECURE=TRUE`

> Hinweis: Die README nennt bewusst nur die wichtigsten Punkte – die aktuelle, ausführlichste Doku ist die `.env.example`.

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
- `nginx/` – Nginx Reverse Proxy Configs (`local.conf`, `prod.conf`)
- `certs/` – TLS-Zertifikate für Nginx (`local/` und `prod/`)
- `media/` – lokale Medienbibliothek (wird nicht versioniert gedacht)
- `instance/` – Laufzeitdaten (z.B. Cache-Dateien)
- `tests/` – Tests

---

## Security / Betriebshinweise

- 🔒 **Primär fürs Heimnetz gedacht:** Die App wird security-seitig laufend verbessert, um langfristig auch öffentliche Nutzung zu ermöglichen. Trotzdem: bitte nicht „einfach so“ ohne zusätzliche Maßnahmen ins Internet hängen.
- 🔐 **HTTPS via Nginx:** Compose-Setups laufen standardmäßig über HTTPS (auch lokal). Zertifikate müssen vorhanden sein (siehe oben).
- 🧷 **`SECRET_KEY` setzen:** erforderlich für sichere Sessions/CSRF.
- 🧭 **Pfadvalidierung:** Routen dürfen nur innerhalb von `MEDIA_ROOT` auf echte Dateien zugreifen (Schutz vor Directory Traversal).
- ⏱️ **Rate Limiting:** Flask-Limiter nutzt Redis und hilft gegen Missbrauch.

---

## Roadmap (Auswahl)

- ✅ 🛡️ Erweiterte Brute-Force-Protection mit DB-Unterstuetzung (umgesetzt)
- ✅ 🔜 Media-Serving via Nginx (z.B. `X-Accel-Redirect`) statt `send_file` in Flask (umgesetzt)
- ✅ ‍💼 Admin-Dashboard fuer mehrere Nutzer (umgesetzt)
- ⏯️ Wiedergabefortschritt in der DB speichern (wie weit wurde geschaut)
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
