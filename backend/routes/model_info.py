"""
Neo-Dock -- backend/routes/model_info.py
==========================================
GET /model/info      -- mimari + parametre + egitim config'i
GET /model/history   -- epoch tablosu (Tr MSE/RMSE/R, Val MSE/RMSE/R)
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["model"])

ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = ROOT / "ml" / "model_final"


@router.get("/model/info", summary="Model mimarisi + parametreleri")
def model_info():
    cfg_path = MODEL_DIR / "config.json"
    if not cfg_path.exists():
        raise HTTPException(404, "config.json bulunamadi")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    # parametre sayisi: ya config'te ya da hesapla
    try:
        import torch, sys
        sys.path.insert(0, str(ROOT))
        from ml.model_v2 import NeoDockGNN
        m = NeoDockGNN(
            hidden_dim=cfg["hidden_dim"],
            n_lig_layers=cfg["n_layers"],
            dropout=cfg.get("dropout", 0.1),
            use_pocket=cfg.get("use_pocket", False),
            node_dim=cfg.get("node_dim", 79),
            edge_dim=cfg.get("edge_dim", 10),
        )
        total = sum(p.numel() for p in m.parameters())
    except Exception:
        total = None

    return {
        "version":          cfg.get("version", "v1.0"),
        "architecture":     "GINEConv Graph Neural Network",
        "hidden_dim":       cfg["hidden_dim"],
        "n_layers":         cfg["n_layers"],
        "dropout":          cfg.get("dropout", 0.1),
        "node_dim":         cfg.get("node_dim", 79),
        "edge_dim":         cfg.get("edge_dim", 10),
        "pooling":          "mean + max concat",
        "total_parameters": total,
        "dataset": {
            "name":  "PDBBind v2020",
            "train": cfg.get("train_size"),
            "val":   cfg.get("val_size"),
            "test":  cfg.get("test_size"),
        },
        "training": {
            "epochs_trained":    cfg.get("epochs_trained"),
            "train_time_s":      cfg.get("train_time_seconds"),
            "best_val_rmse":     cfg.get("best_val_rmse"),
            "test_rmse":         cfg.get("test_rmse"),
            "test_pcc":          cfg.get("test_pcc"),
        },
    }


@router.get("/model/history", summary="Epoch-bazli egitim metrikleri")
def model_history():
    h_path = MODEL_DIR / "history.json"
    if not h_path.exists():
        raise HTTPException(404, "history.json yok (egitim yapilmamis)")
    history = json.loads(h_path.read_text(encoding="utf-8"))
    return {
        "n_epochs": len(history),
        "columns": ["epoch", "tr_mse", "tr_rmse", "tr_pcc", "tr_r2",
                    "val_mse", "val_rmse", "val_pcc", "val_r2", "lr"],
        "history": history,
    }
