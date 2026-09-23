import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import Base, engine
from backend.routes import shorten, analytics, redirect
from backend.utils.logger import logger

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI Scalable URL Shortener Application Started Successfully.")
    yield
    logger.info("FastAPI Scalable URL Shortener Application Shutting Down.")

app = FastAPI(
    title="Scalable URL Shortener API",
    description="Production-ready URL Shortener System with Analytics, Expiration, Rate Limiting & Base62 Generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(shorten.router)
app.include_router(analytics.router)

# Frontend Path
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Mount Static Directory
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "URL Shortener System"}

@app.get("/", tags=["Frontend SPA"], include_in_schema=False)
@app.get("/app", tags=["Frontend SPA"])
def serve_frontend_spa():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend index.html not found"}

# Root-level Static Asset Helpers for SPA serving
@app.get("/styles.css", include_in_schema=False)
def serve_styles():
    css_file = os.path.join(frontend_path, "styles.css")
    if os.path.exists(css_file):
        return FileResponse(css_file, media_type="text/css")
    return Response(status_code=404)

@app.get("/script.js", include_in_schema=False)
def serve_script():
    js_file = os.path.join(frontend_path, "script.js")
    if os.path.exists(js_file):
        return FileResponse(js_file, media_type="application/javascript")
    return Response(status_code=404)

@app.get("/favicon.ico", include_in_schema=False)
def serve_favicon():
    return Response(status_code=204)

# Register Redirect Router LAST so /{short_code} does not override static assets or API endpoints
app.include_router(redirect.router)
