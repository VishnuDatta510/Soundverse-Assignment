"""
Integration tests for /play endpoints.

The TestClient uses the in-memory SQLite DB defined in conftest.py.
Env vars (DATABASE_URL, API_KEY) are set in conftest.py before any app import.
"""
import os

from fastapi.testclient import TestClient

HEADERS = {"X-API-Key": os.environ["API_KEY"]}


def test_missing_api_key_returns_401(client: TestClient):
    response = client.get("/play")
    assert response.status_code == 401


def test_wrong_api_key_returns_401(client: TestClient):
    response = client.get("/play", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_list_clips_returns_list(client: TestClient):
    response = client.get("/play", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1


def test_clip_has_required_fields(client: TestClient):
    response = client.get("/play", headers=HEADERS)
    clip = response.json()[0]
    for field in ("id", "title", "description", "genre", "duration", "audio_url"):
        assert field in clip, f"Missing field: {field}"


def test_post_play_creates_clip(client: TestClient):
    payload = {
        "title": "Test Track",
        "description": "A test clip",
        "genre": "electronic",
        "duration": "15s",
        "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    }
    response = client.post("/play", json=payload, headers=HEADERS)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Track"
    assert data["id"] is not None


def test_post_play_invalid_url_returns_422(client: TestClient):
    payload = {
        "title": "Bad URL",
        "genre": "pop",
        "duration": "10s",
        "audio_url": "not-a-url",
    }
    response = client.post("/play", json=payload, headers=HEADERS)
    assert response.status_code == 422


def test_stats_returns_play_count(client: TestClient):
    clips = client.get("/play", headers=HEADERS).json()
    clip_id = clips[0]["id"]
    response = client.get(f"/play/{clip_id}/stats", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "play_count" in data
    assert isinstance(data["play_count"], int)


def test_stats_404_for_missing_clip(client: TestClient):
    response = client.get("/play/99999/stats", headers=HEADERS)
    assert response.status_code == 404


def test_stream_404_for_missing_clip(client: TestClient):
    response = client.get("/play/99999/stream", headers=HEADERS)
    assert response.status_code == 404
