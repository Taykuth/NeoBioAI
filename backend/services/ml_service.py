"""
Neo-Dock — backend/services/ml_service.py
==========================================
ML modelini backend'e bağlayan servis katmanı.

Singleton pattern: Model yükleme ~2-5 saniye sürer.
Uygulama başlarken bir kez yükle, sonra bellekte tut.

Mock mod: Model ağırlıkları yoksa deterministik sahte değer üretir.
Bu sayede GNN eğitilmeden önce API tam çalışır.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

_model  = None
_device = None
_config = None
_loaded = False


def _load_model():
    global _model, _device, _config, _loaded

    if _loaded:
        return _model is not None

    # Model dizinlerini ara
    for model_dir_name in ["model_final", "model_week3", "model_week1"]:
        model_dir = ROOT / "ml" / model_dir_name
        if model_dir.exists():
            break
    else:
        logger.warning("Model dizini bulunamadı — mock mod aktif (API çalışır, gerçek GNN değil)")
        _loaded = True
        return False

    weights = model_dir / "model_final.pt"
    if not weights.exists():
        weights = model_dir / "best_model.pt"
    cfg_file = model_dir / "config.json"

    if not weights.exists():
        logger.warning(f"Model ağırlıkları bulunamadı: {model_dir} — mock mod aktif")
        _loaded = True
        return False

    try:
        import torch
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if cfg_file.exists():
            _config = json.loads(cfg_file.read_text())
        else:
            _config = {"hidden_dim": 128, "n_layers": 4, "dropout": 0.1, "use_pocket": False}

        from ml.model_v2 import NeoDockGNN
        _model = NeoDockGNN(
            hidden_dim=_config["hidden_dim"],
            n_lig_layers=_config["n_layers"],
            dropout=0.0,
            use_pocket=_config.get("use_pocket", False),
            node_dim=_config.get("node_dim", 79),
            edge_dim=_config.get("edge_dim", 10),
        ).to(_device)

        state = torch.load(str(weights), map_location=_device, weights_only=True)
        _model.load_state_dict(state)
        _model.eval()

        logger.info(f"[OK] Model yuklendi: {weights.name} | Params: {_model.count_parameters():,} | Device: {_device}")
        _loaded = True
        return True

    except Exception as e:
        logger.error(f"Model yükleme hatası: {e}")
        _loaded = True
        return False


def predict_binding_affinity(smiles: str, pdb_id: Optional[str] = None) -> dict:
    """
    SMILES → binding affinity tahmini (pKd).

    pKd yorumu:
      < 5   → zayıf bağlanma
      5–7   → orta
      7–9   → güçlü (ilaç adayı)
      > 9   → çok güçlü (umut verici)
    """
    t_start = time.time()
    model_available = _load_model()

    if not model_available or _model is None:
        runtime_ms = (time.time() - t_start) * 1000
        return {
            "predicted_pKd": _mock_prediction(smiles),
            "confidence":    0.0,
            "runtime_ms":    round(runtime_ms, 2),
            "model_version": "mock-v1",
            "is_mock":       True,
            "error":         None,
        }

    # SMILES validasyon
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {
                "predicted_pKd": None,
                "confidence":    0.0,
                "runtime_ms":    round((time.time() - t_start) * 1000, 2),
                "model_version": _config.get("version", "unknown"),
                "is_mock":       False,
                "error":         f"Geçersiz SMILES: {smiles[:50]}",
            }
    except ImportError:
        pass

    # Gerçek inference
    try:
        import torch
        from ml.features import smiles_to_graph
        from torch_geometric.data import Batch

        graph = smiles_to_graph(smiles)
        batch = Batch.from_data_list([graph]).to(_device)

        with torch.no_grad():
            pred = _model(batch).squeeze(-1).item()

        pred = max(pred, 0.0)
        runtime_ms = (time.time() - t_start) * 1000

        return {
            "predicted_pKd": round(pred, 3),
            "confidence":    0.0,
            "runtime_ms":    round(runtime_ms, 2),
            "model_version": _config.get("version", "week3"),
            "is_mock":       False,
            "error":         None,
        }
    except Exception as e:
        logger.error(f"Inference hatası: {e}")
        return {
            "predicted_pKd": None,
            "confidence":    0.0,
            "runtime_ms":    round((time.time() - t_start) * 1000, 2),
            "model_version": "error",
            "is_mock":       False,
            "error":         str(e),
        }


def batch_predict(smiles_list: list) -> list:
    _load_model()
    return [predict_binding_affinity(smi) for smi in smiles_list]


def get_model_info() -> dict:
    _load_model()
    if _model is None:
        return {"loaded": False, "version": "mock", "params": 0, "mode": "mock"}
    return {
        "loaded":     True,
        "version":    _config.get("version", "unknown") if _config else "unknown",
        "params":     _model.count_parameters() if _model else 0,
        "device":     str(_device),
        "use_pocket": _config.get("use_pocket", False) if _config else False,
        "mode":       "gnn",
    }


def _mock_prediction(smiles: str) -> float:
    """Deterministik mock — SMILES uzunluğuna göre sabit değer."""
    np.random.seed(len(smiles) % 100 + sum(ord(c) for c in smiles[:10]) % 17)
    return round(float(np.random.uniform(4.5, 9.0)), 3)
