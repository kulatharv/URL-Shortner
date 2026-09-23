# 🔗 Scalable URL Shortener System with Analytics (FastAPI + Frontend)

A production-grade, highly scalable web application that converts long URLs into short, shareable links with HTTP 302 redirection, atomic click tracking, real-time analytics, Base62 collision handling, rate limiting, link expiration, and an interactive glassmorphic dashboard.

---

## 🏗️ System Architecture

```
                       ┌─────────────────────────┐
                       │  Frontend Dashboard SPA │
                       │   (HTML5 / CSS3 / JS)   │
                       └────────────┬────────────┘
                                    │  HTTP / REST API
                                    ▼
                       ┌─────────────────────────┐
                       │     FastAPI Backend     │
                       │ (Uvicorn ASGI Engine)   │
                       └────────────┬────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
┌──────────────────────┐┌──────────────────────┐┌──────────────────────┐
│  Database Layer      ││ Base62 Code Generator││ IP Rate Limiter &    │
│(SQLite / PostgreSQL) ││ & Collision Retries  ││ Input Validator      │
└──────────────────────┘└──────────────────────┘└──────────────────────┘
```

---

## 🚀 Core Features

- **Base62 Collision-Free Short Codes**: 6–8 character random Base62 encoding (`a-z`, `A-Z`, `0-9`) with configurable max retries.
- **Custom Alias Support**: Custom URL aliases (e.g. `shortpulse/my-custom-name`) with duplicate conflict detection (HTTP 409).
- **Atomic Click Tracking**: High-concurrency SQL update queries preventing race conditions (`UPDATE urls SET click_count = click_count + 1, last_accessed_at = ...`).
- **Link Expiration Handling**: Configurable expiration timestamp per link with HTTP 410 Gone status.
- **Strict Input Security**: Protocol verification (`http://` / `https://`) and loopback self-shortening prevention.
- **IP Rate Limiting**: Sliding window rate limiting protecting API endpoints from abuse (HTTP 429).
- **Environment Configuration**: Multi-environment config via `.env` for `DATABASE_URL` and `BASE_URL`.
- **Real-Time Analytics & Pagination**: Inspect click counts, created date, last access, expiration status, and paginated history (`GET /api/links?page=1&limit=10`).
- **Interactive SPA Frontend**: Dark mode glassmorphism UI with copy-to-clipboard, client-side QR code generator, toast notifications, and analytics inspector.

---

## 📡 API Specification

### 1. Create Short URL
- **Method**: `POST /api/shorten`
- **Request Body**:
  ```json
  {
    "url": "https://example.com/long/path",
    "custom_alias": "dev-docs",
    "expires_in_minutes": 60
  }
  ```
- **Response** (HTTP 201 Created):
  ```json
  {
    "short_url": "http://127.0.0.1:8000/dev-docs",
    "short_code": "dev-docs",
    "original_url": "https://example.com/long/path",
    "created_at": "2026-09-23T17:00:00Z",
    "expires_at": "2026-09-23T18:00:00Z"
  }
  ```

### 2. Redirection
- **Method**: `GET /{short_code}`
- **Behavior**: Atomically increments `click_count`, updates `last_accessed_at`, and returns HTTP 302 Temporary Redirect to target URL.
- **Error Codes**:
  - `404 Not Found`: Code does not exist.
  - `410 Gone`: Link has expired.

### 3. Link Analytics
- **Method**: `GET /api/analytics/{short_code}`
- **Response** (HTTP 200 OK):
  ```json
  {
    "original_url": "https://example.com/long/path",
    "short_code": "dev-docs",
    "short_url": "http://127.0.0.1:8000/dev-docs",
    "clicks": 42,
    "created_at": "2026-09-23T17:00:00Z",
    "expires_at": "2026-09-23T18:00:00Z",
    "last_accessed_at": "2026-09-23T17:05:12Z",
    "is_expired": false
  }
  ```

### 4. List Short Links (Paginated)
- **Method**: `GET /api/links?page=1&limit=10`
- **Response**: Paginated list of analytics items ordered by newest first.

---

## 🛠️ Quick Start & Running Locally

### Prerequisites
- Python 3.9+
- pip

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Create or edit `.env`:
```env
DATABASE_URL=sqlite:///./url_shortener.db
BASE_URL=http://127.0.0.1:8000
RATE_LIMIT_PER_MINUTE=10
DEFAULT_CODE_LENGTH=6
MAX_RETRIES=5
```

### 3. Run FastAPI Application
```bash
uvicorn backend.main:app --reload --port 8000
```

- **Interactive API Documentation**: Access Swagger UI at `http://127.0.0.1:8000/docs`
- **Frontend SPA Dashboard**: Access in browser at `http://127.0.0.1:8000/app` or open `frontend/index.html` directly.

---

## 🧪 Running Unit Tests

Run the complete test suite using pytest:
```bash
python -m pytest -v
```

Tests cover:
- Valid URL shortening
- Invalid URL & loopback self-shortening prevention (HTTP 400)
- Custom alias duplicate conflicts (HTTP 409)
- Redirection (HTTP 302) & atomic click count validation
- Missing code (HTTP 404) & expired links (HTTP 410)
- Rate limiting enforcement (HTTP 429)
- Paginated link listing

---

## ☁️ 100% Free Hosting Guide

You can host both the FastAPI backend and frontend **100% free** using **Render.com** or **Koyeb**.

### Option 1: Render.com (Recommended - Free Web Service)

1. **Push your repository to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - URL Shortener System"
   git remote add origin https://github.com/your-username/url-shortener.git
   git push -u origin main
   ```
2. **Deploy on Render**:
   - Go to [render.com](https://render.com) and sign up for a free account.
   - Click **New +** -> **Web Service**.
   - Connect your GitHub repository.
   - Set **Build Command**: `pip install -r requirements.txt`
   - Set **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Add Environment Variable:
     - `BASE_URL`: `https://your-app-name.onrender.com` (Set to your Render app URL)
   - Click **Create Web Service**.

Render will deploy your app, and your shortener will be live for free at `https://your-app-name.onrender.com/app`!

---

### Option 2: Decoupled (Vercel Frontend + Render Backend)

- **Backend (Render.com)**: Deploy FastAPI web service on Render (free).
- **Frontend (Vercel)**:
  1. Go to [vercel.com](https://vercel.com) and import your `frontend/` folder.
  2. Set `BASE_URL` in `frontend/script.js` to point to your backend API URL on Render.
  3. Deploy in 1-click for free.

