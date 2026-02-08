# VideoPlayer

**VideoPlayer** is a lightweight Flask web app for playing **local video files** directly in the browser. It is designed for typical series/anime folder structures (seasons/episodes) and is operated **via Docker Compose with PostgreSQL, Redis, and Nginx (reverse proxy)**.

---

## Features (current)

- 📚 **Library/Browse**: Browse media under `media/` (including pagination)
- 🔎 **Search**: Title and file name search
- 🎬 **Watch page**: Playback in browser (frontend via Video.js)
- 👤 **Authentication**: Login-protected use
- 🛡️ **Brute-force protection**: Account lockout after too many login attempts (DB fields)
- 🗄️ **Database**: Persistence for app data
- ⏱️ **Rate limiting**: via Flask limiter + Redis backend
- 🧩 **Modular structure**: Blueprints, utils, and config separated
- 🐳 **Docker-ready**: Start via Compose (base + local/prod overrides)
- 🔐 **HTTPS (also local)**: via Nginx reverse proxy


**Note:** There is **no transcoding** ("direct play"). Whether a video can be played depends on your browser's codecs.


---

## Quickstart (Docker Compose, lokal via HTTPS)

**Requirements:** Docker + Docker Compose

### 1) Clone repository

```bash
git clone https://github.com/tvdw07/VideoPlayer.git
cd VideoPlayer
```

### 2) Create `.env`

The easiest way is to copy the sample file:

```bash
cp .env.example .env
```

At least adjust `SECRET_KEY` and the database credentials.

> Configuration is done via the Compose files and `.env`. More detailed documentation will follow; the variables are already commented on in detail in `.env.example`.

### 3) Create local TLS certificates

For the local Nginx proxy, the setup expects certificates to be located at:

- `certs/local/fullchain.pem`
- `certs/local/privkey.key`

Create the folder:

```bash
mkdir -p certs/local
```

Then you can generate a self-signed certificate (OpenSSL):

```bash
# execute in the project root
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout certs/local/privkey.key \
  -out certs/local/fullchain.pem \
  -subj "/CN=localhost"
```

**Important:** Your browser will not automatically trust the certificate. For the "green lock," you need a local CA (e.g., `mkcert`) or you can import the certificate manually.

### 4) Build & start container (recreate)

If you really want to start from scratch (including removing volumes/DB data), use this flow:

```bash
docker compose down -v
docker compose -f compose.yml -f compose.local.yml up -d --build
```

> Note: `down -v` deletes **volumes** (e.g., Postgres data). Only use this if you really want to.

### 5) Create admin user

Then create an admin user (once):

```bash
docker compose exec videoplayer flask create-user admin --admin
```

### 6) Restart container

To ensure everything reloads properly:

```bash
docker compose -f compose.yml -f compose.local.yml restart
```

### 7) Open in browser

- https://localhost/

(HTTP on port 80 is redirected to HTTPS.)

**Add media:** Place your files/folders under `media/` (will be mounted in the container).

---

## Production (Note)

There is a separate override for a productive environment:

```bash
docker compose -f compose.yml -f compose.prod.yml up -d --build
```

The prod setup expects certificates under:

- `certs/prod/fullchain.pem`
- `certs/prod/privkey.key`
---

## System requirements

The app is run via Docker. The following components are required:

- **Docker** (version 20.10+)
- **Docker Compose**
- At least **512 MB of free RAM** (recommended: 1 GB+)

---

## Configuration

- Central environment variables: `.env` (template: `.env.example`)
- Compose files:
  - `compose.yml` (base: app + Postgres + Redis)
  - `compose.local.yml` (local: Nginx + mounts for `nginx/local.conf` and `certs/local`)
- `compose.prod.yml` (prod: Nginx + mounts for `nginx/prod.conf` and `certs/prod`)

**Important variables (excerpt):**

- `SECRET_KEY` – Session/CSRF protection (**required**)
- `DATABASE_URL` – SQLAlchemy URI (points to service `postgres` in Docker setup)
- `RATELIMIT_STORAGE_URI` – Redis URI (usually `redis://redis:6379/0` in the Docker setup)
- `AUTH_ENABLED` – Auth master switch (**must** be `TRUE` in prod; otherwise, the app will refuse to start)
- Cookie settings for HTTPS:
- `SESSION_COOKIE_SECURE=TRUE`
- `REMEMBER_COOKIE_SECURE=TRUE`

> Note: The README deliberately only mentions the most important points – the current, most detailed documentation is the `.env.example`.
---

## Media Structure

The app expects media to be located under `MEDIA_ROOT` (default `media/`). Typical structure:

- `media/anime/<title>/…S01E001….mp4`
- `media/series/<title>/Season 01/…`
- `media/movies/<title>.mp4`

Recognition is designed for series/episode patterns (e.g., `S01E001`).

---

## Project structure (brief)

- `videoplayer/` – App-Code (App-Factory, Config, Utils)
- `videoplayer/routes/` – Blueprints/Routes (`browse`, `watch`, `media`, `settings`)
- `templates/` – Jinja2 Templates
- `static/` – CSS/JS (u.a. `static/js/player.js`)
- `nginx/` – Nginx Reverse Proxy Configs (`local.conf`, `prod.conf`)
- `certs/` – TLS certificates for Nginx (`local/` and `prod/`)
- `media/` – local media library (not intended to be versioned)
- `instance/` – Runtime data (e.g., cache files)
- `tests/` – Tests

---

## Security / Operating Instructions

- 🔒 **Primarily intended for home networks:** The app is constantly being improved in terms of security to enable public use in the long term. Nevertheless, please do not connect to the internet "just like that" without taking additional measures.
- 🔐 **HTTPS via Nginx:** Compose setups run over HTTPS by default (even locally). Certificates must be available (see above).
- 🧷 **Set `SECRET_KEY`:** required for secure sessions/CSRF.
- 🧭 **Path validation:** Routes may only access real files within `MEDIA_ROOT` (protection against directory traversal).
- ⏱️ **Rate limiting:** Flask-Limiter uses Redis and helps prevent abuse.

---

## Roadmap (selection)

- ✅ 🛡️ Enhanced brute force protection with DB support (implemented)
- ✅ 🔜 Media serving via Nginx (e.g., `X-Accel-Redirect`) instead of `send_file` in Flask (implemented)
- ✅ ‍💼 Admin dashboard for multiple users (implemented)
- ⏯️ Save playback progress in the DB (how far has been watched)
- 🧾 Extended logging
- 🧠 Improved readability through more comments
- 🧪 More tests
- ⚙️ Extended settings
- 🎨 Design update (optional)
- ⬆️ Optional: Allow uploads to the server

---

## Contributing

Contributions are welcome 😊

- **Bugs/ideas:** please submit as a GitHub issue with reproduction steps
- **Pull requests:** preferably small and focused (with a short description)
- **Tests:** if possible, add/update appropriate tests


---

## Legal notice

Please only use media for which you have the necessary rights. This project only provides a local playback interface.
