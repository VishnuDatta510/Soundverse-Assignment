# SoundVerse Play API

A lightweight audio-preview library built with FastAPI. The service lets clients browse a catalogue of short sound clips, stream their audio, and track play counts - backed by PostgreSQL and instrumented with Prometheus metrics.

---

## Table of Contents

- [Overview](#overview)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Authentication](#authentication)
- [Monitoring](#monitoring)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [CI/CD](#cicd)
- [Environment Variables](#environment-variables)

---

## Overview

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL (SQLite fallback for local dev) |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Metrics | Prometheus via `starlette-exporter` |
| Deployment | Render |
| CI | GitHub Actions |

The database is seeded automatically on first startup with six royalty-free audio clips sourced from public-domain repositories. No manual migration step is required.

---

## API Reference

All `/play` routes require an `X-API-Key` header. See [Authentication](#authentication).

### GET /play
Returns the full catalogue of available sound clips.

**Response**
```json
[
  {
    "id": 1,
    "title": "Forest Rain",
    "description": "Gentle rain falling through a dense forest canopy.",
    "genre": "ambient",
    "duration": "30s",
    "audio_url": "https://..."
  }
]
```

---

### GET /play/{id}/stream
Streams the clip's audio as `audio/mpeg`. Play count is incremented in the background after the response begins, so streaming latency is not affected.

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | ID of the clip to stream |

---

### GET /play/{id}/stats
Returns metadata and the current play count for a single clip.

**Response**
```json
{
  "id": 1,
  "title": "Forest Rain",
  "description": "...",
  "genre": "ambient",
  "duration": "30s",
  "audio_url": "https://...",
  "play_count": 42
}
```

---

### POST /play
Adds a new clip entry. Accepts metadata only - no file upload required.

**Request body**
```json
{
  "title": "My Clip",
  "description": "Optional description",
  "genre": "electronic",
  "duration": "45s",
  "audio_url": "https://example.com/clip.mp3"
}
```

---

### GET /metrics
Exposes Prometheus metrics. Not protected by API key - intended for internal scraping only.

---

### GET /
Health check. Returns `{"service": "SoundVerse", "status": "ok"}`.

---

## Project Structure

```
app/
  core/
    config.py        # Pydantic settings, loaded from .env
    security.py      # API key dependency
  routers/
    play.py          # All /play route handlers
  services/
    clips.py         # Business logic: CRUD, streaming, seeding
  database.py        # Engine setup, session factory
  models.py          # SQLAlchemy ORM model (AudioClip)
  schemas.py         # Pydantic request/response schemas
  seed_data.py       # Seed definitions for six default clips
  main.py            # App factory, middleware, lifespan
tests/               # Pytest test suite
.github/workflows/   # GitHub Actions CI pipeline
render.yaml          # Render deployment configuration
requirements.txt
```

---

## Database Schema

**Table: `audio_clips`**

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER | Primary key, auto-increment |
| `title` | VARCHAR(255) | Required |
| `description` | TEXT | Optional |
| `genre` | VARCHAR(100) | Required |
| `duration` | VARCHAR(20) | e.g. `"30s"` |
| `audio_url` | TEXT | Public URL to the MP3 file |
| `play_count` | INTEGER | Defaults to `0`, incremented on each stream |

---

## Authentication

Every `/play` route is protected by a static API key sent in the request header:

```
X-API-Key: <your_api_key>
```

The key is configured via the `API_KEY` environment variable. Requests with a missing or incorrect key receive a `403 Forbidden` response.

---

## Monitoring

The app exposes a `/metrics` endpoint in the Prometheus text format, powered by `starlette-exporter`. The following metrics are tracked out of the box:

- **`starlette_requests_total`** - total HTTP requests, labelled by method, path, and status code
- **`starlette_request_duration_seconds`** - response latency histogram per endpoint
- **Derived** - stream counts per clip ID can be filtered from `starlette_requests_total` using the `/play/{id}/stream` path label

To visualise metrics locally, point a Prometheus instance at `http://localhost:8000/metrics` and connect Grafana to that Prometheus data source.

---

## Local Development

**Prerequisites:** Python 3.12+, PostgreSQL (or use the SQLite fallback).

```bash
# 1. Clone and enter the repository
git clone <repo-url>
cd soundverse

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set DATABASE_URL and API_KEY

# 5. Run the development server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive documentation is at `http://localhost:8000/docs`.

**SQLite fallback:** If you want to run without a PostgreSQL instance, set `FORCE_SQLITE_LOCAL=1` in your `.env`. The app will use a local `soundverse.db` file instead.

---

## Deployment

The service is deployed on **Render** using `render.yaml`.

The start command binds to `0.0.0.0` on port `10000` as required by Render:

```
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

The following environment variables must be set in the Render dashboard before deploying:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (e.g. Supabase pooler URL on port 6543) |
| `API_KEY` | Secret key for `X-API-Key` authentication |

The database schema is created and seeded automatically on application startup.

---

## CI/CD

A GitHub Actions workflow at `.github/workflows/ci.yml` runs on every push and pull request to `main`:

1. **Lint** - `flake8` checks code style
2. **Test** - `pytest` runs the full test suite with a SQLite in-memory database

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes* | - | PostgreSQL connection string |
| `API_KEY` | Yes | - | Static API key for all `/play` routes |
| `APP_NAME` | No | `SoundVerse` | Application name shown in docs |
| `FORCE_SQLITE_LOCAL` | No | `0` | Set to `1` to force SQLite regardless of `DATABASE_URL` |
| `AUTO_SQLITE_FALLBACK` | No | `true` | Automatically fall back to SQLite if PostgreSQL is unreachable |

\* Not required if `FORCE_SQLITE_LOCAL=1`.

Copy `.env.example` to `.env` and fill in the values. Never commit `.env` to version control - it is listed in `.gitignore`.