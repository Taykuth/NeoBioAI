"""
Neo-Dock — backend/routes/health.py
"""

import time
import sys
from fastapi import APIRouter
from backend.services.ml_service import get_model_info

router = APIRouter(tags=["system"])
_start_time = time.time()


@router.get("/health", summary="Sistem sağlık kontrolü")
def health():
    model_info = get_model_info()
    return {
        "status":        "ok",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "python_version": sys.version.split()[0],
        "model":          model_info,
    }
