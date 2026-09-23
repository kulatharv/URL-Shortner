import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db, engine as prod_engine
from backend.models import URLItem
from backend.main import app

# Ensure tables are created on test execution
Base.metadata.create_all(bind=prod_engine)

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_db():
    db = next(get_db())
    db.query(URLItem).delete()
    db.commit()
    yield
    db.query(URLItem).delete()
    db.commit()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_shorten_valid_url():
    response = client.post(
        "/api/shorten",
        json={"url": "https://example.com/some/long/path?query=1"},
        headers={"X-Bypass-RateLimit": "true"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert "short_url" in data
    assert data["original_url"] == "https://example.com/some/long/path?query=1"

def test_shorten_invalid_url():
    response = client.post(
        "/api/shorten",
        json={"url": "invalid-url-with-no-protocol-or-host-:::"},
        headers={"X-Bypass-RateLimit": "true"}
    )
    assert response.status_code == 400

def test_shorten_self_referential_url():
    response = client.post(
        "/api/shorten",
        json={"url": "http://127.0.0.1:8000/api/shorten"},
        headers={"X-Bypass-RateLimit": "true"}
    )
    assert response.status_code == 400
    assert "service domain" in response.json()["detail"]

def test_custom_alias_success_and_conflict():
    # 1. Success
    alias = "my-custom-link"
    res1 = client.post(
        "/api/shorten",
        json={"url": "https://github.com", "custom_alias": alias},
        headers={"X-Bypass-RateLimit": "true"}
    )
    assert res1.status_code == 201
    assert res1.json()["short_code"] == alias

    # 2. Duplicate alias Conflict (409)
    res2 = client.post(
        "/api/shorten",
        json={"url": "https://google.com", "custom_alias": alias},
        headers={"X-Bypass-RateLimit": "true"}
    )
    assert res2.status_code == 409
    assert "already in use" in res2.json()["detail"]

def test_redirection_and_analytics():
    # Create short link
    short_res = client.post(
        "/api/shorten",
        json={"url": "https://python.org"},
        headers={"X-Bypass-RateLimit": "true"}
    )
    short_code = short_res.json()["short_code"]

    # Redirect (HTTP 302)
    red_res = client.get(f"/{short_code}", follow_redirects=False)
    assert red_res.status_code == 302
    assert red_res.headers["location"] == "https://python.org"

    # Verify click increment in analytics
    analytics_res = client.get(f"/api/analytics/{short_code}")
    assert analytics_res.status_code == 200
    adata = analytics_res.json()
    assert adata["clicks"] == 1
    assert adata["last_accessed_at"] is not None

def test_non_existent_short_code():
    res = client.get("/nonexistent999", follow_redirects=False)
    assert res.status_code == 404

def test_expired_link():
    # Directly inject an expired item into testing DB
    db = next(get_db())
    expired_item = URLItem(
        original_url="https://expired-example.com",
        short_code="exp123",
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db.add(expired_item)
    db.commit()

    # Attempt redirect -> should return 410 Gone
    res = client.get("/exp123", follow_redirects=False)
    assert res.status_code == 410
    assert "expired" in res.json()["detail"].lower()

def test_paginated_links():
    # Populate 3 links
    for i in range(3):
        client.post(
            "/api/shorten",
            json={"url": f"https://example{i}.com"},
            headers={"X-Bypass-RateLimit": "true"}
        )

    res = client.get("/api/links?page=1&limit=2")
    assert res.status_code == 200
    pdata = res.json()
    assert pdata["total"] == 3
    assert len(pdata["items"]) == 2
    assert pdata["page"] == 1
    assert pdata["limit"] == 2

def test_rate_limiting():
    # Make 11 requests without bypass header
    rate_limited = False
    for i in range(12):
        res = client.post(
            "/api/shorten",
            json={"url": f"https://ratelimittest{i}.com"}
        )
        if res.status_code == 429:
            rate_limited = True
            break
    assert rate_limited is True
