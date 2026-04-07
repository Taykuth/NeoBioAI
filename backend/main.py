"""
NeoBioAI — backend/main.py
==========================
FastAPI uygulaması giriş noktası.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# Servisleri başlat
from backend.auth_jwt.auth import router as auth_router
from backend.routes.predict import router as predict_router
from backend.routes.health import router as health_router
from backend.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıç/bitiş olayları."""
    # Başlangıçta ML modelini yükle
    from backend.services.ml_service import _load_model
    _load_model()
    print("[OK] NeoBioAI API hazir -- http://localhost:8000/docs")
    yield
    print("NeoBioAI API kapatiliyor...")


app = FastAPI(
    title="NeoBioAI API",
    description="Yapay zeka tabanli ilac kesfi ve baglama afinitesi tahmini servisi",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)

# Router'ları kaydet
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(health_router)


@app.get("/", tags=["root"])
def root():
    return {
        "name": "NeoBioAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "description": "GINEConv tabanli protein-ligand baglama afinitesi tahmini",
    }
